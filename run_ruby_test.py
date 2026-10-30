import os
import re
import functools
import sublime
import sublime_plugin
import subprocess


def containing_folder(file_name, folders):
  """Return the deepest open folder containing this path, using literal paths."""
  matches = []
  for folder in folders:
    if os.path.splitdrive(file_name)[0].lower() != os.path.splitdrive(folder)[0].lower():
      continue
    relative = os.path.relpath(file_name, folder)
    if relative != os.pardir and not relative.startswith(os.pardir + os.sep):
      matches.append(folder)
  return max(matches, key=len) if matches else None


def quote_argument(value):
  if sublime.platform() == 'windows':
    quoted = subprocess.list2cmdline([value])
    return quoted if quoted.startswith('"') else '"' + quoted + '"'
  return "'" + value.replace("'", "'\"'\"'") + "'"


def output_panel(window):
  if hasattr(window, 'find_output_panel'):
    panel = window.find_output_panel('exec')
    if panel is not None:
      return panel
  return window.get_output_panel('exec')

class ShowInPanel:
  def __init__(self, window):
    self.window = window

  def display_results(self):
    self.panel = output_panel(self.window)
    self.window.run_command("show_panel", {"panel": "output.exec"})
    self.panel.settings().set("color_scheme", THEME)
    self.panel.set_syntax_file(SYNTAX)
    if HIDE_PANEL:
      self.window.run_command("hide_panel")
    self.panel.settings().set("color_scheme", THEME)


class ShowInScratch:
  def __init__(self, window):
    self.window = window
    self.active_for = 0
    self.copied_until = 0

  def display_results(self):
    self.panel = output_panel(self.window)
    self.window.run_command("hide_panel")
    self.view = self.window.new_file()
    self.view.set_name("Test Results")
    self.view.set_scratch(True)
    self.view.set_read_only(False)

    self.view.set_syntax_file(SYNTAX)
    self.view.settings().set("color_scheme", THEME)
    self.view.set_read_only(True)
    self.poll_copy()

  def poll_copy(self):
    # FIXME HACK: Stop polling after one minute
    if self.active_for < 60000:
      self.active_for += 50
      sublime.set_timeout(self.copy_stuff, 50)

  def append(self, content):
    self.view.set_read_only(False)
    self.view.run_command('append', {'characters': content, 'force': True, 'scroll_to_end': True})
    self.view.set_read_only(True)
    self.view.set_viewport_position((self.view.size(), self.view.size()), True)

  def copy_stuff(self):
    if not self.view.is_valid():
      return
    size = self.panel.size()
    content = self.panel.substr(sublime.Region(self.copied_until, size))
    if content:
      self.copied_until = size
      self.append(content)
    self.poll_copy()

class ShowPanels:
  def __init__(self, window):
    self.window = window

  def split(self):
    if self.window.num_groups() > 1:
      self.window.focus_group((self.window.active_group() + 1) % self.window.num_groups())
      return
    if sublime.load_settings('RubyTest.sublime-settings').get('split_orientation', 'vertical') == 'horizontal':
      layout = {"cols": [0.0, 1.0], "rows": [0.0, 0.5, 1.0], "cells": [[0, 0, 1, 1], [0, 1, 1, 2]]}
    else:
      layout = {
                          "cols": [0.0, 0.5, 1.0],
                          "rows": [0.0, 1.0],
                          "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
                      }
    self.window.run_command('set_layout', layout)
    self.window.focus_group(1)

class TestMethodMatcher(object):
  def find_first_match_in(self, test_file_content):
    # Read forward, then select the last declaration regardless of test style.
    declarations = list(re.finditer(
      r"^\s*(?:def\s+(test\w+)|test\s+([\"'])(.+?)\2\s+do|should\s+([\"'])(.+?)\4\s+do)",
      test_file_content, re.MULTILINE))
    if declarations:
      match = declarations[-1]
      if match.group(1):
        return match.group(1)
      if match.group(3):
        return 'test_' + re.sub(r'\s+', '_', match.group(3))
      return '/' + re.escape(match.group(5)) + '/'

class RubyTestSettings:
  def __init__(self):
    self.settings = sublime.load_settings("RubyTest.sublime-settings")

  def __getattr__(self, name):
    if not self.settings.has(name):
      raise AttributeError(name)
    window = sublime.active_window()
    view = window.active_view() if window else None
    value = view.settings().get(name) if view else None
    if value is not None:
      return lambda **kwargs: value.format(**kwargs)
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
    global COMMAND_PREFIX; COMMAND_PREFIX = ""
    global SAVE_ON_RUN; SAVE_ON_RUN = s.get("save_on_run")
    global SYNTAX; SYNTAX = s.get('syntax')
    global THEME; THEME = s.get('theme')
    global TERMINAL_ENCODING; TERMINAL_ENCODING = s.get('terminal_encoding')


  def command_prefix(self, working_dir):
    s = sublime.load_settings("RubyTest.sublime-settings")
    global COMMAND_PREFIX
    COMMAND_PREFIX = ""
    chruby  = s.get("check_for_chruby")
    rbenv   = s.get("check_for_rbenv")
    rvm     = s.get("check_for_rvm")
    bundler = s.get("check_for_bundler")
    spring  = s.get("check_for_spring")
    if chruby or rbenv or rvm: self.chruby_or_rbenv_or_rvm(s, chruby, rbenv, rvm)
    if spring: self.spring_support()
    if bundler: self.bundler_support(working_dir)

  def spring_support(self):
    global COMMAND_PREFIX
    COMMAND_PREFIX = COMMAND_PREFIX + " spring "

  def chruby_or_rbenv_or_rvm(self, s, chruby, rbenv, rvm):
    chruby_sh = os.path.expanduser('/usr/local/opt/chruby/share/chruby/chruby.sh')

    which_rbenv = os.popen('which rbenv').read().split('\n')[0]
    brew_rbenv = '/usr/local/bin/rbenv'
    rbenv_cmd = os.path.expanduser('~/.rbenv/bin/rbenv')

    rvm_cmd = os.path.expanduser('~/.rvm/bin/rvm-auto-ruby')

    if os.path.isfile(brew_rbenv): rbenv_cmd = brew_rbenv
    elif os.path.isfile(which_rbenv): rbenv_cmd = which_rbenv

    global COMMAND_PREFIX
    if chruby and os.path.isfile(chruby_sh):
      COMMAND_PREFIX = 'source ' + chruby_sh + ' && chruby `[ -f .ruby-version ] && cat .ruby-version || ruby` && '
    elif rbenv and self.is_executable(rbenv_cmd):
      COMMAND_PREFIX = rbenv_cmd + ' exec'
    elif rvm and self.is_executable(rvm_cmd):
      COMMAND_PREFIX = rvm_cmd + ' -S'

  def bundler_support(self, project_root):
    gemfile_path = os.path.join(project_root, 'Gemfile')

    global COMMAND_PREFIX
    if not COMMAND_PREFIX:
      COMMAND_PREFIX = ""

    if os.path.isfile(gemfile_path):
      COMMAND_PREFIX =  COMMAND_PREFIX + " bundle exec "

  def save_all(self):
    if SAVE_ON_RUN:
      self.window().run_command("save_all")

  def is_executable(self, path):
    return os.path.isfile(path) and os.access(path, os.X_OK)

  def save_test_run(self, command, working_dir):
    s = sublime.load_settings("RubyTest.last-run")
    s.set("last_test_run", command)
    s.set("last_test_working_dir", working_dir)

    sublime.save_settings("RubyTest.last-run")

  def run_shell_command(self, command, working_dir):
    if not command:
      return False
    if not working_dir or not os.path.isdir(working_dir):
      sublime.error_message('RubyTest working directory no longer exists: ' + str(working_dir))
      return False
    self.command_prefix(working_dir)
    if BEFORE_CALLBACK:
      os.system(BEFORE_CALLBACK)
    self.save_test_run(command, working_dir)
    if AFTER_CALLBACK:
      command += " ; " + AFTER_CALLBACK
    if COMMAND_PREFIX:
      command = COMMAND_PREFIX + ' ' + command
    options = {
      "working_dir": working_dir,
      "file_regex": r"([^ ]*\.rb):?(\d*)",
      "encoding": TERMINAL_ENCODING
    }
    options['env'] = sublime.load_settings('RubyTest.sublime-settings').get('env', {})
    if int(sublime.version().split('.')[0]) < 3000:
      options.update(cmd=[command], shell=True)
    else:
      options['shell_cmd'] = command
    self.window().run_command("exec", options)
    self.display_results()
    return True

  def display_results(self):
    display = ShowInScratch(self.window()) if USE_SCRATCH else ShowInPanel(self.window())
    display.display_results()

  def window(self):
    return self.view.window()

  class BaseFile(object):
    def __init__(self, file_name, partition_folder="", project_folder=None):
      self.folder_name, self.file_name = os.path.split(file_name)
      self.partition_folder = partition_folder
      self.absolute_path = file_name
      self.project_folder = project_folder
    def parent_dir_name(self):
      head_dir, tail_dir = os.path.split(self.folder_name)
      return tail_dir
    def verify_syntax_command(self): return None
    def possible_alternate_files(self): return []
    def run_all_tests_command(self): return None
    def get_project_root(self): return self.folder_name
    def find_project_root(self):
      if self.partition_folder:
        to_find = os.sep + os.path.normpath(self.partition_folder) + os.sep
        if self.project_folder:
          # Search inside the open project first, so test/unit/test still has
          # the same root as test/unit. A test folder can itself be open.
          project = self.project_folder.rstrip(os.sep)
          if (project + os.sep).endswith(to_find):
            return os.path.normpath(project[:-len(to_find) + 1] + os.sep)
          relative = os.sep + os.path.relpath(self.absolute_path, self.project_folder)
          prefix, found, _ = relative.partition(to_find)
          if found:
            return os.path.normpath(self.project_folder + prefix)
        project_root, found, _ = self.absolute_path.rpartition(to_find)
        if found:
          if project_root.endswith(':'):
            return project_root + os.sep
          return project_root or os.path.abspath(os.sep)
      return self.project_folder or self.folder_name
    def relative_file_path(self):
      return os.path.relpath(self.absolute_path, self.get_project_root())
    def get_current_line_number(self, view):
      char_under_cursor = view.sel()[0].a
      return view.rowcol(char_under_cursor)[0] + 1
    def features(self): return []

  class AnonymousFile(BaseFile):
    def __init__(self):
      super(BaseRubyTask.AnonymousFile, self).__init__('')

  class RubyFile(BaseFile):
    def verify_syntax_command(self): return RubyTestSettings().ruby_verify_command(file_name=self.relative_file_path())
    def possible_alternate_files(self): return [self.file_name.replace(".rb", "_spec.rb"), self.file_name.replace(".rb", "_test.rb"), "test_" + self.file_name, self.file_name.replace(".rb", ".feature")]
    def features(self): return ["verify_syntax", "switch_to_test", "rails_generate", "extract_variable"]

  class UnitFile(RubyFile):
    def possible_alternate_files(self):
      if self.file_name.startswith('test_'):
        return [self.file_name[5:]]
      return [self.file_name[:-8] + '.rb']
    def run_all_tests_command(self): return RubyTestSettings().run_ruby_unit_command(relative_path=self.relative_file_path())
    def run_single_test_command(self, view):
      region = view.sel()[0]
      line_region = view.line(region)
      text_string = view.substr(sublime.Region(0, line_region.end()))
      test_name = TestMethodMatcher().find_first_match_in(text_string)
      if test_name is None:
        sublime.error_message("No test name!")
        return None
      return RubyTestSettings().run_single_ruby_unit_command(relative_path=self.relative_file_path(), test_name=test_name, test_name_quoted=quote_argument(test_name), line_number=self.get_current_line_number(view))
    def features(self): return super(BaseRubyTask.UnitFile, self).features() + ["run_test"]
    def get_project_root(self): return self.find_project_root()

  class CucumberFile(BaseFile):
    def possible_alternate_files(self): return list( set( [self.file_name.replace(".feature", ".rb"), self.file_name.replace(".feature", "_steps.rb")] ) )
    def run_all_tests_command(self): return RubyTestSettings().run_cucumber_command(relative_path=self.relative_file_path())
    def run_single_test_command(self, view): return RubyTestSettings().run_single_cucumber_command(relative_path=self.relative_file_path(), line_number=self.get_current_line_number(view))
    def features(self): return ["switch_to_test", "run_test"]
    def get_project_root(self): return self.find_project_root()

  class RSpecFile(RubyFile):
    def possible_alternate_files(self): return list( set( [self.file_name.replace("_spec.rb", ".rb"), self.file_name.replace(".haml_spec.rb", ".haml"), self.file_name.replace(".erb_spec.rb", ".erb")] ) - set([self.file_name]) )
    def run_all_tests_command(self): return RubyTestSettings().run_rspec_command(relative_path=self.relative_file_path())
    def run_single_test_command(self, view): return RubyTestSettings().run_single_rspec_command(relative_path=self.relative_file_path(), line_number=self.get_current_line_number(view))
    def features(self): return super(BaseRubyTask.RSpecFile, self).features() + ["run_test"]
    def get_project_root(self): return self.find_project_root()

  class ErbFile(BaseFile):
    def verify_syntax_command(self): return RubyTestSettings().erb_verify_command(file_name=self.relative_file_path())
    def can_verify_syntax(self): return True
    def possible_alternate_files(self): return [self.file_name.replace(".erb", ".erb_spec.rb")]
    def features(self): return ["verify_syntax", "switch_to_test"]

  class HamlFile(BaseFile):
    def possible_alternate_files(self): return [self.file_name.replace(".haml", ".haml_spec.rb")]
    def features(self): return ["switch_to_test"]

  class CucumberStepsFile(BaseFile):
    def possible_alternate_files(self): return [self.file_name.replace("_steps.rb", ".feature")]
    def features(self): return ["switch_to_test"]

  def file_type(self, file_name = None, load_config = True):
    if load_config:
      self.load_config()
    file_name = file_name or self.view.file_name()
    if not file_name: return BaseRubyTask.AnonymousFile()
    name = os.path.basename(file_name)
    project_folder = containing_folder(file_name, self.window().folders())
    if name.endswith('_spec.rb'):
      return BaseRubyTask.RSpecFile(file_name, RSPEC_UNIT_FOLDER, project_folder)
    # Rails source models such as app/models/exercise_test.rb are code.
    parts = os.path.normpath(file_name).split(os.sep)
    is_app_code = 'app' in parts and RUBY_UNIT_FOLDER not in parts
    if name.endswith('_test.rb') and not is_app_code:
      return BaseRubyTask.UnitFile(file_name, RUBY_UNIT_FOLDER, project_folder)
    elif name.startswith('test_') and name.endswith('.rb') and not is_app_code:
      return BaseRubyTask.UnitFile(file_name, RUBY_UNIT_FOLDER, project_folder)
    elif name.endswith('.feature'):
      return BaseRubyTask.CucumberFile(file_name, CUCUMBER_UNIT_FOLDER, project_folder)
    elif name.endswith('_steps.rb'):
      return BaseRubyTask.CucumberStepsFile(file_name)
    elif name.endswith('.rb'):
      return BaseRubyTask.RubyFile(file_name)
    elif name.endswith('.erb'):
      return BaseRubyTask.ErbFile(file_name)
    elif name.endswith('.haml'):
      return BaseRubyTask.HamlFile(file_name)
    else:
      return BaseRubyTask.BaseFile(file_name)


class RunSingleRubyTest(BaseRubyTask):
  def is_enabled(self): return 'run_test' in self.file_type().features()
  def run(self, args):
    self.load_config()
    self.save_all()
    file = self.file_type()
    command = file.run_single_test_command(self.view)
    self.run_shell_command(command, file.get_project_root())


class RunAllRubyTest(BaseRubyTask):
  def is_enabled(self): return 'run_test' in self.file_type().features()
  def run(self, args):
    self.load_config()
    self.save_all()
    file = self.file_type(self.view.file_name())
    command = file.run_all_tests_command()
    if self.run_shell_command(command, file.get_project_root()):
      pass
    else:
      sublime.error_message("Only *_test.rb, test_*.rb, *_spec.rb, *.feature files supported!")


class RunLastRubyTest(BaseRubyTask):
  def load_last_run(self):
    self.load_config()
    self.save_all()
    s = sublime.load_settings("RubyTest.last-run")
    return (s.get("last_test_run"), s.get("last_test_working_dir"))

  def run(self, args):
    last_command, working_dir = self.load_last_run()
    self.run_shell_command(last_command, working_dir)


class RunRubyTestSuite(BaseRubyTask):
  def run(self, edit):
    self.load_config()
    self.save_all()
    file = self.file_type()
    root = file.find_project_root() if 'run_test' in file.features() else None
    if not root and self.view.file_name():
      root = containing_folder(self.view.file_name(), self.window().folders()) or file.folder_name
    if not root:
      folders = self.window().folders()
      root = folders[0] if folders else None
    self.run_shell_command(RubyTestSettings().run_ruby_suite_command(), root)


class CancelRubyTest(BaseRubyTask):
  def run(self, edit):
    self.window().run_command('exec', {'kill': True})


class ScrollRubyTestOutputToTop(BaseRubyTask):
  def run(self, edit):
    panel = output_panel(self.window())
    panel.set_viewport_position((0, 0), False)

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
  def is_enabled(self, split_view=False): return 'switch_to_test' in self.file_type().features()
  def run(self, args, split_view=False):
    self.load_config()
    possible_alternates = self.file_type().possible_alternate_files()
    alternates = self.project_files(lambda file: file in possible_alternates)

    source_parts = os.path.dirname(self.view.file_name()).split(os.sep)
    def score(alternate):
      count = 0
      for source, target in zip(reversed(source_parts), reversed(os.path.dirname(alternate).split(os.sep))):
        if source != target:
          break
        count += 1
      return count
    if alternates:
      best = max(score(alternate) for alternate in alternates)
      alternates = sorted(set(alternate for alternate in alternates if score(alternate) == best))

    if alternates:
      if split_view:
        ShowPanels(self.window()).split()
      if len(alternates) == 1:
        self.open_alternate(alternates[0], split_view)
      else:
        callback = functools.partial(self.on_selected, alternates, split_view)
        self.window().show_quick_panel(alternates, callback)
    else:
      GenerateTestFile(self.window(), split_view).doIt()

  def open_alternate(self, path, split_view):
    window = self.window()
    group = window.active_group()
    view = window.open_file(path)
    if split_view:
      window.set_view_index(view, group, -1)
      window.focus_view(view)

  def on_selected(self, alternates, split_view, index):
    if index == -1:
      return

    self.open_alternate(alternates[index], split_view)

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
    if self.window().active_panel() == 'output.exec':
      self.window().run_command('hide_panel', {'panel': 'output.exec'})
    else:
      self.window().run_command("show_panel", {"panel": "output.exec"})

class RubyExtractVariable(BaseRubyTask):
  def is_enabled(self): return 'extract_variable' in self.file_type().features()
  def run(self, args):
    for selection in self.view.sel():
      self.window().show_input_panel("Variable Name: ", '', lambda name, selection=selection: self.generate(selection, name), None, None)

  def generate(self, selection, name):
    self.view.run_command('ruby_replace_with_variable', {'start': selection.begin(), 'end': selection.end(), 'name': name})


class RubyReplaceWithVariable(sublime_plugin.TextCommand):
  def run(self, edit, start, end, name):
    selection = sublime.Region(start, end)
    extracted = self.view.substr(selection)
    line = self.view.line(selection)
    white_space = re.match(r"\s*", self.view.substr(line)).group()
    self.view.replace(edit, selection, name)
    self.view.insert(edit, line.begin(), white_space + name + " = " + extracted + "\n")

class GenerateTestFile:
  relative_paths = []
  full_torelative_paths = {}
  rel_path_start = 0

  def __init__(self, window, split_view):
    self.window = window
    self.split_view = split_view

  def doIt(self):
    self.build_relative_paths()
    self.window.show_quick_panel(self.relative_paths, self.dir_selected)

  def build_relative_paths(self):
      folders = self.active_project(self.window.folders())
      view = self.window.active_view()
      self.relative_paths = []
      self.full_torelative_paths = {}
      for path in folders:
          rootfolders = os.path.split(path)[-1]
          self.rel_path_start = len(os.path.split(path)[0]) + 1
          if self.is_valid_path(path):
            self.full_torelative_paths[rootfolders] = path
            self.relative_paths.append(rootfolders)

          for base, dirs, files in os.walk(path):
              for dir in dirs:
                  relative_path = os.path.join(base, dir)[self.rel_path_start:]
                  if self.is_valid_path(relative_path):
                    self.full_torelative_paths[relative_path] = os.path.join(base, dir)
                    self.relative_paths.append(relative_path)

  def active_project(self, folders):
    folder = containing_folder(self.current_file(), folders)
    return [folder] if folder else folders

  def is_valid_path(self, path):
    if re.search(self.test_path_re(), self.current_file()):
      parts = os.path.normpath(path).split(os.sep)
      return any(part in parts for part in ('app', 'lib', 'extras')) and not any(part in parts for part in ('assets', 'views', 'vendor'))
    else:
      return re.search(self.test_path_re(), path)

  def test_path_re(self):
    return r'(^|[/\\])(?:' + '|'.join(re.escape(folder) for folder in (RUBY_UNIT_FOLDER, RSPEC_UNIT_FOLDER, CUCUMBER_UNIT_FOLDER)) + r')([/\\]|$)'

  def current_file(self):
    return self.window.active_view().file_name()

  def dir_selected(self, selected_index):
      if selected_index != -1:
          self.selected_dir = self.relative_paths[selected_index]
          self.selected_dir = self.full_torelative_paths[self.selected_dir]
          self.window.show_input_panel("File name", self.suggest_file_name(self.selected_dir), self.file_name_input, None, None)

  def suggest_file_name(self, path):
    current_file = os.path.split(self.current_file())[-1]
    return self.set_file_name(path, current_file)

  def set_file_name(self, path, current_file):
    if re.search(self.test_path_re(), self.current_file()):
      if current_file.endswith('_spec.rb'):
        return current_file[:-8] + '.rb'
      if current_file.startswith('test_'):
        return current_file[5:]
      return re.sub(r'_test\.rb$|_spec\.rb$|\.feature$', '.rb', current_file)
    else:
      return current_file.replace('.rb', self.detect_test_type(path))

  def detect_test_type(self, path):
    parts = os.path.normpath(path).split(os.sep)
    if RUBY_UNIT_FOLDER in parts:
      return '_test.rb'
    if RSPEC_UNIT_FOLDER in parts:
      return '_spec.rb'
    if CUCUMBER_UNIT_FOLDER in parts:
      return '.feature'

  def file_name_input(self, file_name):
      full_path = os.path.join(self.selected_dir, file_name)

      if os.path.lexists(full_path):
          sublime.error_message('File already exists:\n%s' % full_path)
          return
      else:
          self.create_and_open_file(full_path)

  def create_and_open_file(self, path):
      if not os.path.exists(path):
          self.create(path)

      if self.split_view:
        ShowPanels(self.window).split()

      self.window.open_file(path)

  def create(self, filename):
      base, filename = os.path.split(filename)
      self.create_folder(base)

  def create_folder(self, base):
      if not os.path.exists(base):
          parent = os.path.split(base)[0]
          if not os.path.exists(parent):
              self.create_folder(parent)
          os.mkdir(base)

class GenerateFile(sublime_plugin.WindowCommand):
  def run(self):
    GenerateNewFile(self.window).doIt()

class GenerateNewFile(GenerateTestFile):
  def __init__(self, window):
    self.window = window
    self.split_view = False

  def active_project(self, folders):
    return folders

  def is_valid_path(self, path):
    return not any(part.startswith('.') for part in os.path.normpath(path).split(os.sep) if part)

  def suggest_file_name(self, path):
    return ""


class RubyTestKeybindings(sublime_plugin.EventListener):
  def on_query_context(self, view, key, operator, operand, match_all):
    if key == 'ruby_test_keybindings':
      enabled = sublime.load_settings('RubyTest.sublime-settings').get('enable_keybindings', True)
      if operator == sublime.OP_EQUAL:
        return enabled == operand
      if operator == sublime.OP_NOT_EQUAL:
        return enabled != operand
