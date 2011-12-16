import os
import re
import thread
import subprocess
import functools
import time
import sublime
import sublime_plugin

class AsyncProcess(object):
  def __init__(self, cmd, listener):
    self.cmd = cmd
    self.listener = listener
    print "DEBUG_EXEC: " + self.cmd
    self.proc = subprocess.Popen([self.cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if self.proc.stdout:
      thread.start_new_thread(self.read_stdout, ())
    if self.proc.stderr:
      thread.start_new_thread(self.read_stderr, ())

  def read_stdout(self):
    while True:
      data = os.read(self.proc.stdout.fileno(), 2**15)
      if data != "":
        sublime.set_timeout(functools.partial(self.listener.append_data, self.proc, data), 0)
      else:
        self.proc.stdout.close()
        self.listener.is_running = False
        break

  def read_stderr(self):
    while True:
      data = os.read(self.proc.stderr.fileno(), 2**15)
      if data != "":
        sublime.set_timeout(functools.partial(self.listener.append_data, self.proc, data), 0)
      else:
        self.proc.stderr.close()
        self.listener.is_running = False
        break

class StatusProcess(object):
  def __init__(self, msg, listener):
    self.msg = msg
    self.listener = listener
    thread.start_new_thread(self.run_thread, ())

  def run_thread(self):
    progress = ""
    while True:
      if self.listener.is_running:
        if len(progress) >= 10:
          progress = ""
        progress += "."
        sublime.set_timeout(functools.partial(self.listener.update_status, self.msg, progress), 0)
        time.sleep(1)
      else:
        break

class BaseRubyTask(sublime_plugin.WindowCommand):
  def load_config(self):
    s = sublime.load_settings("RubyTest.sublime-settings")
    global RUBY_UNIT; RUBY_UNIT = s.get("ruby_unit_exec")
    global CUCUMBER_UNIT; CUCUMBER_UNIT = s.get("ruby_cucumber_exec")
    global RSPEC_UNIT; RSPEC_UNIT = s.get("ruby_rspec_exec")
    global RUBY_UNIT_FOLDER; RUBY_UNIT_FOLDER = s.get("ruby_unit_folder")
    global CUCUMBER_UNIT_FOLDER; CUCUMBER_UNIT_FOLDER = s.get("ruby_cucumber_folder")
    global RSPEC_UNIT_FOLDER; RSPEC_UNIT_FOLDER = s.get("ruby_rspec_folder")

  def save_test_run(self, ex, file_name):
    s = sublime.load_settings("RubyTest.last-run")
    s.set("last_test_run", ex)
    s.set("last_test_file", file_name)

    sublime.save_settings("RubyTest.last-run")

  def show_tests_panel(self):
    if not hasattr(self, 'output_view'):
      self.output_view = self.window.get_output_panel("tests")
    self.clear_test_view()
    self.window.run_command("show_panel", {"panel": "output.tests"})

  def clear_test_view(self):
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)

  def append_data(self, proc, data):
    str = data.decode("utf-8")
    str = str.replace('\r\n', '\n').replace('\r', '\n')

    selection_was_at_end = (len(self.output_view.sel()) == 1
      and self.output_view.sel()[0]
        == sublime.Region(self.output_view.size()))
    self.output_view.set_read_only(False)
    edit = self.output_view.begin_edit()
    self.output_view.insert(edit, self.output_view.size(), str)
    if selection_was_at_end:
      self.output_view.show(self.output_view.size())
    self.output_view.end_edit(edit)
    self.output_view.set_read_only(True)

  def start_async(self, caption, executable):
    self.is_running = True
    self.proc = AsyncProcess(executable, self)
    StatusProcess(caption, self)

  def update_status(self, msg, progress):
    sublime.status_message(msg + " " + progress)

  def project_path(self, path, command):
    return "cd " + path + " && " + command

  class BaseFile:
    def __init__(self, file_name): self.folder_name, self.file_name = os.path.split(file_name)
    def verify_syntax_command(self): return None
    def wrap_in_cd(self, path, command): return "cd " + path + " && " + command
    def possible_alternate_files(self): return []
    def run_all_tests_command(self): return None
    def run_from_project_root(self, partition_folder, command, options = ""):
      folder_name, test_folder, file_name = os.path.join(self.folder_name, self.file_name).partition(partition_folder)
      return self.wrap_in_cd(folder_name, command + " " + test_folder + file_name + options)
    def get_current_line_number(self, view):
      char_under_cursor = view.sel()[0].a
      return view.rowcol(char_under_cursor)[0] + 1

  class RubyFile(BaseFile):
    def verify_syntax_command(self): return self.wrap_in_cd(self.folder_name, "ruby -c " + self.file_name)
    def possible_alternate_files(self): return [self.file_name.replace(".rb", "_spec.rb"), self.file_name.replace(".rb", "_test.rb"), self.file_name.replace(".rb", ".feature")]

  class UnitFile(RubyFile):
    def possible_alternate_files(self): return [self.file_name.replace("_test.rb", ".rb")]
    def run_all_tests_command(self): return self.run_from_project_root(RUBY_UNIT_FOLDER, RUBY_UNIT)
    def run_single_test_command(self, view):
      region = view.sel()[0]
      line_region = view.line(region)
      text_string = view.substr(sublime.Region(region.begin() - 2000, line_region.end()))
      text_string = text_string.replace("\n", "\\N")
      text_string = text_string[::-1]
      match_obj = re.search('\s?([a-zA-Z_\d]+tset)\s+fed', text_string) # 1st search for 'def test_name'
      if not match_obj:
        match_obj = re.search('\s?(\"[a-zA-Z_\s\d]+\"\s+tset)', text_string) # 2nd search for 'test "name"'
      if not match_obj:
        sublime.error_message("No test name!")
        return
      test_name = match_obj.group(1)[::-1]
      test_name = test_name.replace("\"", "").replace(" ", "_") # if test name in 2nd format
      return self.run_from_project_root(RUBY_UNIT_FOLDER, RUBY_UNIT, " -n " + test_name)

  class CucumberFile(BaseFile):
    def possible_alternate_files(self): return [self.file_name.replace(".feature", ".rb")]
    def run_all_tests_command(self): return self.run_from_project_root(CUCUMBER_UNIT_FOLDER, CUCUMBER_UNIT)
    def run_single_test_command(self, view): return self.run_from_project_root(CUCUMBER_UNIT_FOLDER, CUCUMBER_UNIT, " -l " + str(self.get_current_line_number(view)))

  class RSpecFile(RubyFile):
    def possible_alternate_files(self): return [self.file_name.replace("_spec.rb", ".rb")]
    def run_all_tests_command(self): return self.run_from_project_root(RSPEC_UNIT_FOLDER, RSPEC_UNIT)
    def run_single_test_command(self, view): return self.run_from_project_root(RSPEC_UNIT_FOLDER, RSPEC_UNIT, " -l " + str(self.get_current_line_number(view)))

  class ErbFile(BaseFile):
    def verify_syntax_command(self): return self.wrap_in_cd(self.folder_name, "erb -xT - " + self.file_name + " | ruby -c")

  def file_type(self, file_name):
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
      return BaseRubyTask.OtherFile(file_name)

class RunSingleRubyTest(BaseRubyTask):

  def run(self):
    self.load_config()
    view = self.window.active_view()
    file = self.file_type(view.file_name())
    command = file.run_single_test_command(view)
    if command:
      self.save_test_run(command, file.file_name)
      self.show_tests_panel()
      self.is_running = True
      self.proc = AsyncProcess(command, self)
      StatusProcess("Starting tests from file " + file.file_name, self)

class RunAllRubyTest(BaseRubyTask):
  def run(self):
    self.load_config()
    view = self.window.active_view()
    folder_name, file_name = os.path.split(view.file_name())
    file = self.file_type(view.file_name())
    command = file.run_all_tests_command()
    if command:
      self.show_tests_panel()
      self.save_test_run(command, file_name)
      self.is_running = True
      self.proc = AsyncProcess(command, self)
      StatusProcess("Starting tests from file " + file.file_name, self)
    else:
      sublime.error_message("Only *_test.rb, *_spec.rb, *.feature files supported!")


class RunLastRubyTest(BaseRubyTask):
  def load_last_run(self):
    s = sublime.load_settings("RubyTest.last-run")
    global LAST_TEST_RUN; LAST_TEST_RUN = s.get("last_test_run")
    global LAST_TEST_FILE; LAST_TEST_FILE = s.get("last_test_file")

  def run(self):
    self.load_last_run()
    self.show_tests_panel()
    self.is_running = True
    self.proc = AsyncProcess(LAST_TEST_RUN, self)
    StatusProcess("Starting tests from file " + LAST_TEST_FILE, self)

class ShowTestPanel(BaseRubyTask):
  def run(self):
    self.window.run_command("show_panel", {"panel": "output.tests"})

class VerifyRubyFile(BaseRubyTask):
  def run(self):
    view = self.window.active_view()
    file = self.file_type(view.file_name())
    command = file.verify_syntax_command()
    if command:
      self.show_tests_panel()
      self.start_async("Checking syntax of : " + file.file_name, command)
    else:
      sublime.error_message("Only .rb or .erb files supported!")

class SwitchBetweenCodeAndTest(BaseRubyTask):
  def run(self):
    _, file_name = os.path.split(self.window.active_view().file_name())
    possible_alternates = self.file_type(file_name).possible_alternate_files()
    alternates = self.project_files(lambda(file): file in possible_alternates)
    if alternates:
      self.window.open_file(alternates.pop())
    else:
      sublime.error_message("could not find " + str(possible_alternates))

  def walk(self, directory, ignored_directories = []):
    ignored_directories = ['.git', 'vendor']  # Move this into config
    for dir, dirnames, files in os.walk(directory):
      dirnames[:] = [dirname for dirname in dirnames if dirname not in ignored_directories]
      yield dir, dirnames, files

  def project_files(self, file_matcher):
    directories = self.window.folders()
    return [os.path.join(dirname, file) for directory in directories for dirname, _, files in self.walk(directory) for file in filter(file_matcher, files)]
