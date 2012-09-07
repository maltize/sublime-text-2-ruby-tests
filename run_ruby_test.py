import os
import re
import functools
import sublime
import string
import sublime_plugin

class ShowInPanel:
  def __init__(self, window):
    self.window = window

  def display_results(self):
    self.panel = self.window.get_output_panel("exec")
    self.window.run_command("show_panel", {"panel": "output.exec"})
    if HIDE_PANEL:
      self.window.run_command("hide_panel")
    self.panel.settings().set("color_scheme", "Packages/RubyTest/TestConsole.tmTheme")


class ShowInScratch:
  def __init__(self, window):
    self.window = window
    self.active_for = 0
    self.copied_until = 0

  def display_results(self):
    self.panel = self.window.get_output_panel("exec")
    self.window.run_command("hide_panel")
    self.view = self.window.new_file()
    self.view.set_scratch(True)
    self.view.set_name("Test Results")
    self.view.settings().set("color_scheme", "Packages/RubyTest/TestConsole.tmTheme")
    self.view.set_read_only(True)
    self.poll_copy()

  def poll_copy(self):
    # FIXME HACK: Stop polling after one minute
    if self.active_for < 60000:
      self.active_for += 50
      sublime.set_timeout(self.copy_stuff, 50)

  def copy_stuff(self):
    size = self.panel.size()
    content = self.panel.substr(sublime.Region(self.copied_until, size))
    if content:
      self.copied_until = size
      self.view.set_read_only(False)
      edit = self.view.begin_edit()
      self.view.insert(edit, self.view.size(), content)
      self.view.end_edit(edit)
      self.view.set_read_only(True)
    self.poll_copy()

class TestMethodMatcher(object):
  def __init__(self):
    self.matchers = [TestMethodMatcher.UnitTest, TestMethodMatcher.ShouldaTest]
  def find_first_match_in(self, test_file_content):
    for matcher in self.matchers:
      test_name = matcher.find_first_match(test_file_content)
      if test_name:
        return test_name

  class UnitTest(object):
    @staticmethod
    def find_first_match(test_file_content):
      match_obj = re.search('\s?([a-zA-Z_\d]+tset)\s+fed', test_file_content) # 1st search for 'def test_name'
      if match_obj:
        return match_obj.group(1)[::-1]

      match_obj = re.search('\s?[\"\']([a-zA-Z_\"\'\s\d]+)[\"\']\s+tset', test_file_content) # 2nd search for 'test "name"'
      if match_obj:
        test_name = match_obj.group(1)[::-1]
        return "test_%s" % test_name.replace("\"", "\\\"").replace(" ", "_").replace("'", "\\'")

      return None

  class ShouldaTest(object):
    @staticmethod
    def find_first_match(test_file_content):
      match_obj = re.search('\s?(([\"][^\"]*[\"]|[\'][^\']*[\'])\s+dluohs)', test_file_content) # search for 'should "name"'
      if not match_obj:
        return None
      test_name = match_obj.group(1)[::-1]
      return "%s%s%s" % ("/", test_name.replace("should", "").strip(), "/")


class RubyTestSettings:
  def __init__(self):
    self.settings = sublime.load_settings("RubyTest.sublime-settings")

  def __getattr__(self, name):
    if not self.settings.has(name):
      raise AttributeError(name)
    return lambda **kwargs: self.settings.get(name).format(**kwargs)


class BaseRubyTask(sublime_plugin.TextCommand):
  def load_config(self):
    s = sublime.load_settings("RubyTest.sublime-settings")
    global RUBY_UNIT_FOLDER; RUBY_UNIT_FOLDER = s.get("ruby_unit_folder")
    global CUCUMBER_UNIT_FOLDER; CUCUMBER_UNIT_FOLDER = s.get("ruby_cucumber_folder")
    global RSPEC_UNIT_FOLDER; RSPEC_UNIT_FOLDER = s.get("ruby_rspec_folder")
    global USE_SCRATCH; USE_SCRATCH = s.get("ruby_use_scratch")
    global IGNORED_DIRECTORIES; IGNORED_DIRECTORIES = s.get("ignored_directories")
    global HIDE_PANEL; HIDE_PANEL = s.get("hide_panel")
    global BEFORE_CALLBACK; BEFORE_CALLBACK = s.get("before_callback")
    global AFTER_CALLBACK; AFTER_CALLBACK = s.get("after_callback")

    if s.get("save_on_run"):
      self.window().run_command("save_all")

  def save_test_run(self, command, working_dir):
    s = sublime.load_settings("RubyTest.last-run")
    s.set("last_test_run", command)
    s.set("last_test_working_dir", working_dir)

    sublime.save_settings("RubyTest.last-run")

  def run_shell_command(self, command, working_dir):
    if not command:
      return False
    if BEFORE_CALLBACK:
      os.system(BEFORE_CALLBACK)
    if AFTER_CALLBACK:
      command += " ; " + AFTER_CALLBACK
    self.save_test_run(command, working_dir)
    self.view.window().run_command("exec", {
      "cmd": [command],
      "shell": True,
      "working_dir": working_dir,
      "file_regex": r"([^ ]*\.rb):?(\d*)"
    })
    self.display_results()
    return True

  def display_results(self):
    display = ShowInScratch(self.window()) if USE_SCRATCH else ShowInPanel(self.window())
    display.display_results()

  def window(self):
    return self.view.window()

  class BaseFile(object):
    def __init__(self, file_name):
      self.folder_name, self.file_name = os.path.split(file_name)
      self.absolute_path = file_name
    def verify_syntax_command(self): return None
    def possible_alternate_files(self): return []
    def run_all_tests_command(self): return None
    def get_project_root(self): return self.folder_name
    def find_project_root(self, partition_folder):
      to_find = os.sep + partition_folder + os.sep
      project_root, _, _ = self.absolute_path.partition(to_find)
      return project_root
    def relative_file_path(self, partition_folder):
      to_find = os.sep + partition_folder + os.sep
      _, _, relative_path = self.absolute_path.partition(to_find)
      return partition_folder + os.sep + relative_path
    def get_current_line_number(self, view):
      char_under_cursor = view.sel()[0].a
      return view.rowcol(char_under_cursor)[0] + 1
    def features(self): return []

  class AnonymousFile(BaseFile):
    def __init__(self):
      True

  class RubyFile(BaseFile):
    def verify_syntax_command(self): return RubyTestSettings().ruby_verify_command(file_name=self.file_name)
    def possible_alternate_files(self): return [self.file_name.replace(".rb", "_spec.rb"), self.file_name.replace(".rb", "_test.rb"), self.file_name.replace(".rb", ".feature")]
    def features(self): return ["verify_syntax", "switch_to_test", "rails_generate", "extract_variable"]

  class UnitFile(RubyFile):
    def possible_alternate_files(self): return [self.file_name.replace("_test.rb", ".rb")]
    def run_all_tests_command(self): return RubyTestSettings().run_ruby_unit_command(relative_path=self.relative_file_path(RUBY_UNIT_FOLDER))
    def run_single_test_command(self, view):
      region = view.sel()[0]
      line_region = view.line(region)
      text_string = view.substr(sublime.Region(region.begin() - 2000, line_region.end()))
      text_string = text_string.replace("\n", "\\N")
      text_string = text_string[::-1]
      test_name = TestMethodMatcher().find_first_match_in(text_string)
      if test_name is None:
        sublime.error_message("No test name!")
        return None
      return RubyTestSettings().run_single_ruby_unit_command(relative_path=self.relative_file_path(RUBY_UNIT_FOLDER), test_name=test_name)
    def features(self): return super(BaseRubyTask.UnitFile, self).features() + ["run_test"]
    def get_project_root(self): return self.find_project_root(RUBY_UNIT_FOLDER)

  class CucumberFile(BaseFile):
    def possible_alternate_files(self): return [self.file_name.replace(".feature", ".rb")]
    def run_all_tests_command(self): return RubyTestSettings().run_cucumber_command(relative_path=self.relative_file_path(CUCUMBER_UNIT_FOLDER))
    def run_single_test_command(self, view): return RubyTestSettings().run_single_cucumber_command(relative_path=self.relative_file_path(CUCUMBER_UNIT_FOLDER), line_number=self.get_current_line_number(view))
    def features(self): return ["run_test"]
    def get_project_root(self): return self.find_project_root(CUCUMBER_UNIT_FOLDER)

  class RSpecFile(RubyFile):
    def possible_alternate_files(self): return [self.file_name.replace("_spec.rb", ".rb")]
    def run_all_tests_command(self): return RubyTestSettings().run_rspec_command(relative_path=self.relative_file_path(RSPEC_UNIT_FOLDER))
    def run_single_test_command(self, view): return RubyTestSettings().run_single_rspec_command(relative_path=self.relative_file_path(RSPEC_UNIT_FOLDER), line_number=self.get_current_line_number(view))
    def features(self): return super(BaseRubyTask.RSpecFile, self).features() + ["run_test"]
    def get_project_root(self): return self.find_project_root(RSPEC_UNIT_FOLDER)

  class ErbFile(BaseFile):
    def verify_syntax_command(self): return RubyTestSettings().erb_verify_command(file_name=self.file_name)
    def can_verify_syntax(self): return True
    def features(self): return ["verify_syntax"]

  def file_type(self, file_name = None):
    file_name = file_name or self.view.file_name()
    if not file_name: return BaseRubyTask.AnonymousFile()
    if re.search('\w+\_test.rb', file_name):
      return BaseRubyTask.UnitFile(file_name)
    elif re.search('\w+\_spec.rb', file_name):
      return BaseRubyTask.RSpecFile(file_name)
    elif re.search('\w+\.feature', file_name):
      return BaseRubyTask.CucumberFile(file_name)
    elif re.search('\w+\.rb', file_name):
      return BaseRubyTask.RubyFile(file_name)
    elif re.search('\w+\.erb', file_name):
      return BaseRubyTask.ErbFile(file_name)
    else:
      return BaseRubyTask.BaseFile(file_name)


class RunSingleRubyTest(BaseRubyTask):
  def is_enabled(self): return 'run_test' in self.file_type().features()
  def run(self, args):
    self.load_config()
    file = self.file_type()
    command = file.run_single_test_command(self.view)
    self.run_shell_command(command, file.get_project_root())


class RunAllRubyTest(BaseRubyTask):
  def is_enabled(self): return 'run_test' in self.file_type().features()
  def run(self, args):
    self.load_config()
    file = self.file_type(self.view.file_name())
    command = file.run_all_tests_command()
    if self.run_shell_command(command, file.get_project_root()):
      pass
    else:
      sublime.error_message("Only *_test.rb, *_spec.rb, *.feature files supported!")


class RunLastRubyTest(BaseRubyTask):
  def load_last_run(self):
    self.load_config()
    s = sublime.load_settings("RubyTest.last-run")
    return (s.get("last_test_run"), s.get("last_test_working_dir"))

  def run(self, args):
    last_command, working_dir = self.load_last_run()
    self.run_shell_command(last_command, working_dir)

class VerifyRubyFile(BaseRubyTask):
  def is_enabled(self): return 'verify_syntax' in self.file_type().features()
  def run(self, args):
    self.load_config()
    file = self.file_type()
    command = file.verify_syntax_command()
    if self.run_shell_command(command, file.get_project_root()):
      pass
    else:
      sublime.error_message("Only .rb or .erb files supported!")

class SwitchBetweenCodeAndTest(BaseRubyTask):
  def is_enabled(self): return 'switch_to_test' in self.file_type().features()
  def run(self, args, split_view):
    self.load_config()
    possible_alternates = self.file_type().possible_alternate_files()
    alternates = self.project_files(lambda file: file in possible_alternates)
    if alternates:
      if split_view:
        self.window().run_command('set_layout', {
                              "cols": [0.0, 0.5, 1.0],
                              "rows": [0.0, 1.0],
                              "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
                          })
        self.window().focus_group(1)
      if len(alternates) == 1:
        self.window().open_file(alternates.pop())
      else:
        callback = functools.partial(self.on_selected, alternates)
        self.window().show_quick_panel(alternates, callback)
    else:
      sublime.error_message("could not find " + str(possible_alternates))

  def on_selected(self, alternates, index):
    if index == -1:
      return

    self.window().open_file(alternates[index])

  def walk(self, directory):
    for dir, dirnames, files in os.walk(directory):
      dirnames[:] = [dirname for dirname in dirnames if dirname not in IGNORED_DIRECTORIES]
      yield dir, dirnames, files

  def project_files(self, file_matcher):
    directories = self.window().folders()
    return [os.path.join(dirname, file) for directory in directories for dirname, _, files in self.walk(directory) for file in filter(file_matcher, files)]


class RubyRailsGenerate(BaseRubyTask):
  def is_enabled(self): return 'rails_generate' in self.file_type().features()

  def run(self, args, type = "migration"):
    self.window().show_input_panel("rails generate", type + " ", lambda s: self.generate(s), None, None)

  def generate(self, argument):
    command = 'rails generate {thing}'.format(thing=argument)
    self.run_shell_command(command, self.window().folders()[0])

class ShowTestPanel(BaseRubyTask):
  def run(self, args):
    self.window().run_command("show_panel", {"panel": "output.exec"})

class RubyExtractVariable(BaseRubyTask):
  def is_enabled(self): return 'extract_variable' in self.file_type().features()
  def run(self, args):
    for selection in self.view.sel():
      self.window().show_input_panel("Variable Name: ", '', lambda name: self.generate(selection, name), None, None)

  def generate(self, selection, name):
    extracted = self.view.substr(selection)
    line = self.view.line(selection)
    white_space = re.match("\s*", self.view.substr(line)).group()
    edit = self.view.begin_edit()
    try:
      self.view.replace(edit, selection, name)
      self.view.insert(edit, line.begin(), white_space + name + " = " + extracted + "\n")
    finally:
      self.view.end_edit(edit)
