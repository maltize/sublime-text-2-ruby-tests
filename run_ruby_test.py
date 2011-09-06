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
        if len(progress) > 10 * 3:
          progress = ""
        progress += " :)"
        sublime.set_timeout(functools.partial(self.listener.update_status, self.msg, progress), 0)
        time.sleep(1)
      else:
        break

class RunSingleRubyTest(sublime_plugin.WindowCommand):

  global RUBY_UNIT
  RUBY_UNIT = "ruby -Itest "

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

  def update_status(self, msg, progress):
    sublime.status_message(msg + " " + progress)

  def project_path(self, path, command):
    return "cd " + path + " && cd ../.." + " && " + command

  def run(self):
    view = self.window.active_view()
    folder_name, file_name = os.path.split(view.file_name())

    region = view.sel()[0]
    line_region = view.line(region)

    text_string = view.substr(sublime.Region(region.begin() - 2000, line_region.end()))
    text_string = text_string.replace("\n", " ")
    text_string = text_string[::-1]
    match_obj = re.search('\s?([a-zA-Z_]+tset)\s+fed', text_string) # 1st search for 'def test_name'
    if not match_obj:
      match_obj = re.search('\s?(\"[a-zA-Z_\s]+\"\s+tset)', text_string) # 2nd search for 'test "name"'

    if match_obj:
      self.show_tests_panel()

      test_name = match_obj.group(1)[::-1]
      test_name = test_name.replace("\"", "").replace(" ", "_") # if test name in 2nd format
      ex = self.project_path(folder_name, RUBY_UNIT + view.file_name() + " -n " + test_name)

      self.is_running = True
      self.proc = AsyncProcess(ex, self)
      StatusProcess("Starting test " + test_name, self)
    else:
      sublime.error_message("No test name!")

class RunAllRubyTest(RunSingleRubyTest):
  def run(self):
    view = self.window.active_view()
    folder_name, file_name = os.path.split(view.file_name())

    self.show_tests_panel()

    ex = self.project_path(folder_name, RUBY_UNIT + view.file_name())

    self.is_running = True
    self.proc = AsyncProcess(ex, self)
    StatusProcess("Starting tests from file " + file_name, self)

class ShowTestPanel(sublime_plugin.WindowCommand):
  def run(self):
    self.window.run_command("show_panel", {"panel": "output.tests"})

class VerifyRubyFile(RunSingleRubyTest):
  def run(self):
    view = self.window.active_view()
    folder_name, file_name = os.path.split(view.file_name())
    self.show_tests_panel()

    if re.search('\w+\.rb', file_name):
      ex = self.project_path(folder_name, "ruby -c " + view.file_name())
      self.is_running = True
      self.proc = AsyncProcess(ex, self)
      StatusProcess("Checking syntax of : " + file_name, self)

    elif re.search('\w+\.erb', file_name):
      ex = self.project_path(folder_name, "erb -xT - " + view.file_name() + " |ruby -c")
      self.is_running = True
      self.proc = AsyncProcess(ex, self)
      StatusProcess("Checking syntax of : " + file_name, self)

    else:
      sublime.error_message("only .rb or .erb file")
