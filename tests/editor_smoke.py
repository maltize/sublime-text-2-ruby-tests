"""Run from Sublime's console; see docs/validation.md. Uses a dedicated demo window."""
import json
import os
import re
import tempfile
import time
import traceback

import sublime
import sublime_plugin


class EditorSmoke:
    def __init__(self, root):
        self.root = root
        self.window = sublime.active_window()
        self.settings = sublime.load_settings('RubyTest.sublime-settings')
        with open(os.path.join(root, 'RubyTest.sublime-settings')) as source:
            self.defaults = json.load(source)
        self.backup = {key: self.settings.get(key) for key in self.defaults if self.settings.has(key)}
        self.results = []
        self.result_path = os.path.join(tempfile.gettempdir(), 'rubytest-editor-results.json')
        self.window.set_project_data({'folders': [{'path': os.path.join(root, 'examples')}]})
        self.original_layout = self.window.layout()
        self.last_run = sublime.load_settings('RubyTest.last-run')
        self.last_backup = {key: self.last_run.get(key) for key in ('last_test_run', 'last_test_working_dir') if self.last_run.has(key)}
        for key, value in self.defaults.items():
            self.settings.set(key, value)
        self.steps = iter([
            self.nested_syntax, self.nested_single, self.all_tests,
            self.standalone, self.rerun_unsaved, self.scratch,
            self.extract_variable, self.switching, self.horizontal_split,
            self.panel_toggle, self.project_suite, self.environment, self.cancel_start,
        ])

    def require(self, condition, message="Editor check failed"):
        if not condition:
            raise AssertionError(message)

    def record(self, name, **details):
        self.results.append(dict(name=name, passed=True, **details))
        print('RubyTest editor PASS: ' + name)

    def next(self):
        try:
            next(self.steps)()
        except StopIteration:
            self.finish()
        except Exception:
            self.fail()

    def fail(self):
        self.results.append({'passed': False, 'traceback': traceback.format_exc()})
        self.finish()

    def wait(self, predicate, done, timeout=15):
        deadline = time.time() + timeout
        def poll():
            try:
                if predicate():
                    done()
                elif time.time() >= deadline:
                    raise AssertionError('Timed out waiting for editor result')
                else:
                    sublime.set_timeout(poll, 100)
            except Exception:
                self.fail()
        sublime.set_timeout(poll, 100)

    def open(self, relative, callback, line=0):
        view = self.window.open_file(os.path.join(self.root, 'examples', relative))
        def ready():
            self.window.focus_view(view)
            view.sel().clear()
            view.sel().add(sublime.Region(view.text_point(line, 0)))
            callback(view)
        self.wait(lambda: not view.is_loading(), ready)

    def output(self):
        panel = self.window.find_output_panel('exec')
        return panel.substr(sublime.Region(0, panel.size()))

    def run_and_check(self, view, command, expected, name):
        view.run_command(command)
        def complete():
            output = self.output()
            self.require(re.search(expected, output), output)
            self.record(name, output=output)
            self.next()
        self.wait(lambda: '[Finished' in self.output(), complete)

    def nested_syntax(self):
        self.open('test/calculator_test.rb', lambda view: self.run_and_check(view, 'verify_ruby_file', 'Syntax OK', 'nested test syntax'))

    def nested_single(self):
        self.open('test/calculator_test.rb', lambda view: self.run_and_check(view, 'run_single_ruby_test', r'1 runs, [0-9]+ assertions, 0 failures', 'single test with > in its name'), line=14)

    def all_tests(self):
        self.open('test/calculator_test.rb', lambda view: self.run_and_check(view, 'run_all_ruby_test', r'2 runs, [0-9]+ assertions, 0 failures', 'all tests in nested file'))

    def standalone(self):
        self.open('standalone_test.rb', lambda view: self.run_and_check(view, 'run_single_ruby_test', r'1 runs, [0-9]+ assertions, 0 failures', 'standalone test at project root'), line=5)

    def rerun_unsaved(self):
        self.settings.set('check_for_bundler', True)
        view = self.window.new_file()
        self.run_and_check(view, 'run_last_ruby_test', r'1 runs, [0-9]+ assertions, 0 failures', 'rerun from unsaved tab with bundler enabled')

    def scratch(self):
        self.settings.set('ruby_use_scratch', True)
        def run(view):
            view.run_command('run_all_ruby_test')
            scratch = self.window.active_view()
            def complete():
                self.require(scratch.is_scratch())
                self.require(scratch.file_name() is None)
                self.record('scratch output', output=scratch.substr(sublime.Region(0, scratch.size())))
                self.settings.set('ruby_use_scratch', False)
                self.next()
            self.wait(lambda: re.search(r'2 runs, [0-9]+ assertions, 0 failures', scratch.substr(sublime.Region(0, scratch.size()))), complete)
        self.open('test/calculator_test.rb', run)

    def extract_variable(self):
        view = self.window.new_file()
        view.run_command('append', {'characters': '  puts 2 + 3\n'})
        view.run_command('ruby_replace_with_variable', {'start': 7, 'end': 12, 'name': 'sum'})
        self.require(view.substr(sublime.Region(0, view.size())) == '  sum = 2 + 3\n  puts sum\n')
        view.set_scratch(True)
        self.record('extract variable through editor edit token')
        self.next()

    def switching(self):
        def run(view):
            view.run_command('switch_between_code_and_test', {'split_view': False})
            self.require(self.window.active_view().file_name().endswith('test/calculator_test.rb'))
            self.window.active_view().run_command('switch_between_code_and_test', {'split_view': False})
            self.require(self.window.active_view().file_name().endswith('/calculator.rb'))
            self.record('code/test switching both directions')
            self.next()
        self.open('calculator.rb', run)

    def horizontal_split(self):
        self.settings.set('split_orientation', 'horizontal')
        self.window.set_layout({'cols': [0.0, 1.0], 'rows': [0.0, 1.0], 'cells': [[0, 0, 1, 1]]})
        def run(view):
            view.run_command('switch_between_code_and_test', {'split_view': True})
            self.require(self.window.layout()['rows'] == [0.0, 0.5, 1.0])
            self.require(self.window.get_view_index(self.window.active_view())[0] == 1)
            layout = self.window.layout()
            self.window.active_view().run_command('switch_between_code_and_test', {'split_view': True})
            self.require(self.window.layout() == layout)
            self.require(self.window.get_view_index(self.window.active_view())[0] == 0)
            self.record('horizontal split and existing layout preserved')
            self.next()
        self.open('calculator.rb', run)

    def panel_toggle(self):
        view = self.window.active_view()
        self.window.run_command('show_panel', {'panel': 'output.exec'})
        view.run_command('show_test_panel')
        self.require(self.window.active_panel() is None)
        view.run_command('show_test_panel')
        self.require(self.window.active_panel() == 'output.exec')
        view.run_command('scroll_ruby_test_output_to_top')
        self.require(self.window.find_output_panel('exec').viewport_position()[1] == 0)
        self.record('panel toggle and scroll to top')
        self.next()

    def cancel_start(self):
        self.settings.set('run_ruby_suite_command', 'ruby -e "STDOUT.sync=true; puts :rubytest_started; sleep 120"')
        view = self.window.active_view()
        view.run_command('run_ruby_test_suite')
        def cancel():
            view.run_command('cancel_ruby_test')
            def done():
                self.record('project suite command and process cancellation', output=self.output())
                self.next()
            self.wait(lambda: '[Cancelled]' in self.output(), done)
        self.wait(lambda: 'rubytest_started' in self.output(), cancel)

    def project_suite(self):
        self.open('calculator.rb', lambda view: self.run_and_check(view, 'run_ruby_test_suite', r'2 runs, [0-9]+ assertions, 0 failures', 'default Rake project suite from source'))

    def environment(self):
        self.settings.set('env', {'RUBYTEST_SMOKE_ENV': 'available'})
        self.settings.set('run_ruby_suite_command', 'ruby -e "puts ENV.fetch(\'RUBYTEST_SMOKE_ENV\')"')
        self.run_and_check(self.window.active_view(), 'run_ruby_test_suite', 'available', 'explicit environment reaches Ruby')

    def finish(self):
        for key in self.defaults:
            if key in self.backup:
                self.settings.set(key, self.backup[key])
            else:
                self.settings.erase(key)
        for key in ('last_test_run', 'last_test_working_dir'):
            if key in self.last_backup:
                self.last_run.set(key, self.last_backup[key])
            else:
                self.last_run.erase(key)
        sublime.save_settings('RubyTest.last-run')
        self.window.set_layout(self.original_layout)
        with open(self.result_path, 'w') as output:
            json.dump({'sublime_build': sublime.version(), 'results': self.results}, output, indent=2)
        print('RubyTest editor results: ' + self.result_path)


def run(root):
    global smoke
    sublime_plugin.reload_plugin('RubyTest.run_ruby_test')
    smoke = EditorSmoke(root)
    # Command registration is delivered after reload_plugin returns to the loop.
    sublime.set_timeout(smoke.next, 250)
