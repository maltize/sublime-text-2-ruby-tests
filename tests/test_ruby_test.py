"""Regression tests using Sublime doubles; editor checks live in docs/validation.md."""
import json
import ntpath
import os
import re
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import warnings

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'run_ruby_test.py'


class Region:
    def __init__(self, a, b=None):
        self.a, self.b = a, a if b is None else b

    def begin(self):
        return min(self.a, self.b)

    def end(self):
        return max(self.a, self.b)


class Settings(dict):
    def has(self, key):
        return key in self

    def set(self, key, value):
        self[key] = value


class TextCommand:
    def __init__(self, view):
        self.view = view


sublime = types.ModuleType('sublime')
sublime.Region = Region
sublime.OP_EQUAL, sublime.OP_NOT_EQUAL = 0, 1
for name in ('load_settings', 'active_window', 'error_message', 'save_settings', 'set_timeout'):
    setattr(sublime, name, Mock())
sublime.version = Mock(return_value='4215')
sublime.platform = Mock(return_value='osx')
sublime_plugin = types.ModuleType('sublime_plugin')
sublime_plugin.TextCommand = TextCommand
sublime_plugin.WindowCommand = type('WindowCommand', (), {})
sublime_plugin.EventListener = type('EventListener', (), {})
plugin = types.ModuleType('rubytest_under_test')
with patch.dict(sys.modules, sublime=sublime, sublime_plugin=sublime_plugin):
    exec(compile(SOURCE.read_text(), str(SOURCE), 'exec'), plugin.__dict__)


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(json.loads((ROOT / 'RubyTest.sublime-settings').read_text()))
        self.last_run = Settings()
        sublime.load_settings.side_effect = lambda name: self.last_run if name == 'RubyTest.last-run' else self.settings
        sublime.error_message.reset_mock()
        sublime.set_timeout.reset_mock()
        sublime.version.return_value = '4215'
        sublime.platform.return_value = 'osx'
        self.window, self.view = Mock(), Mock()
        self.window.folders.return_value = ['/project']
        self.view.window.return_value = self.window
        self.view.file_name.return_value = '/project/test/calculator_test.rb'
        self.view.settings.return_value = Settings()
        self.window.active_view.return_value = self.view
        sublime.active_window.return_value = self.window
        self.task = plugin.BaseRubyTask(self.view)

    def buffer(self, text, cursor=None):
        cursor = len(text) if cursor is None else cursor
        self.view.sel.return_value = [Region(cursor)]
        line_end = text.find('\n', cursor)
        self.view.line.return_value = Region(text.rfind('\n', 0, cursor) + 1, len(text) if line_end < 0 else line_end)
        self.view.substr.side_effect = lambda region: text[region.begin():region.end()]
        self.view.rowcol.return_value = (text[:cursor].count('\n'), 0)

    def test_source_compiles_without_cached_bytecode_or_warnings(self):
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            compile(SOURCE.read_text(), str(SOURCE), 'exec')

    def test_exact_file_detection(self):
        for name, expected in (
            ('test_invoice_spec.rb', plugin.BaseRubyTask.RSpecFile),
            ('splittest_spec.rb', plugin.BaseRubyTask.RSpecFile),
            ('test_invoice.rb', plugin.BaseRubyTask.UnitFile),
            ('invoice_test.rb', plugin.BaseRubyTask.UnitFile),
            ('invoice_test.rb.bak', plugin.BaseRubyTask.BaseFile),
            ('app/models/exercise_test.rb', plugin.BaseRubyTask.RubyFile),
            ('test/deep/test_invoice_spec.rb', plugin.BaseRubyTask.RSpecFile),
        ):
            with self.subTest(name=name):
                self.assertIs(type(self.task.file_type('/project/' + name)), expected)

    def test_folder_names_do_not_determine_file_type(self):
        self.assertIs(type(self.task.file_type('/project/test_foo.rb/models/item.rb')), plugin.BaseRubyTask.RubyFile)

    def test_standalone_files_use_directory_and_basename(self):
        self.window.folders.return_value = []
        for name in ('calculator_test.rb', 'test_calculator.rb', 'calculator_spec.rb', 'calculator.feature'):
            file = self.task.file_type('/project/' + name)
            self.assertEqual(file.get_project_root(), '/project')
            self.assertEqual(file.relative_file_path(), name)

    def test_standalone_file_uses_containing_open_folder(self):
        file = self.task.file_type('/project/custom/calculator_test.rb')
        self.assertEqual(file.get_project_root(), '/project')
        self.assertEqual(file.relative_file_path(), 'custom/calculator_test.rb')

    def test_configured_folder_wins_over_test_folder_in_window(self):
        self.window.folders.return_value = ['/project/test', '/project', '/project/spec']
        file = self.task.file_type('/project/test/deep/calculator_test.rb')
        self.assertEqual(file.get_project_root(), '/project')
        self.assertEqual(file.relative_file_path(), 'test/deep/calculator_test.rb')

    def test_repeated_test_folder_does_not_change_root(self):
        for folders in (['/project'], ['/project/test']):
            self.window.folders.return_value = folders
            file = self.task.file_type('/project/test/unit/test/calculator_test.rb')
            self.assertEqual(file.get_project_root(), '/project')
            self.assertEqual(file.relative_file_path(), 'test/unit/test/calculator_test.rb')

    def test_custom_folder_and_literal_regex_characters(self):
        self.settings['ruby_unit_folder'] = 'checks[unit]+'
        self.window.folders.return_value = ['/project[demo]+']
        file = self.task.file_type('/project[demo]+/checks[unit]+/calculator_test.rb')
        self.assertEqual(file.get_project_root(), '/project[demo]+')
        self.assertEqual(file.relative_file_path(), 'checks[unit]+/calculator_test.rb')

    def test_windows_paths_and_other_drives(self):
        self.window.folders.return_value = [r'C:\project[demo]+', r'D:\elsewhere']
        with patch.object(plugin.os, 'path', ntpath), patch.object(plugin.os, 'sep', '\\'):
            file = self.task.file_type(r'C:\project[demo]+\test\calculator_test.rb')
            self.assertEqual(file.get_project_root(), r'C:\project[demo]+')
            self.assertEqual(file.relative_file_path(), r'test\calculator_test.rb')
            root_file = self.task.file_type(r'C:\project[demo]+\calculator_spec.rb')
            self.assertEqual(root_file.relative_file_path(), 'calculator_spec.rb')
            drive_root_file = self.task.file_type(r'C:\test\calculator_test.rb')
            self.assertEqual(drive_root_file.get_project_root(), 'C:\\')

    def test_test_prefix_does_not_remove_test_word_in_source_name(self):
        file = self.task.file_type('/project/test/test_exercise_test.rb')
        self.assertEqual(file.possible_alternate_files(), ['exercise_test.rb'])

    def test_nested_open_folder_and_sibling_prefix(self):
        self.assertEqual(plugin.containing_folder('/project/service/a.rb', ['/project', '/project/service']), '/project/service')
        self.assertIsNone(plugin.containing_folder('/project-other/a.rb', ['/project']))

    def test_verify_syntax_uses_path_relative_to_working_directory(self):
        for path in ('test/deep/calculator_test.rb', 'spec/test_calculator_spec.rb', 'plain.rb', 'view.erb'):
            with self.subTest(path=path):
                file = self.task.file_type('/project/' + path)
                command = file.verify_syntax_command()
                self.assertIn('"' + file.relative_file_path() + '"', command)

    def test_single_cucumber_line_is_attached_to_path(self):
        self.buffer('Scenario: example')
        file = self.task.file_type('/project/features/deep/example.feature')
        self.assertEqual(file.run_single_test_command(self.view), 'cucumber "features/deep/example.feature:1"')

    def test_single_test_selects_nearest_style_and_symbols(self):
        self.buffer('def test_first\nend\n' + '# padding\n' * 400 + 'test "sum > 0: works!" do\n  assert true\nend')
        file = self.task.file_type()
        self.assertIn("'test_sum_>_0:_works!'", file.run_single_test_command(self.view))

    def test_def_after_dsl_test_and_cursor_on_declaration(self):
        self.buffer('test "first" do\nend\ndef test_second\n  assert true\nend', 30)
        self.assertEqual(plugin.TestMethodMatcher().find_first_match_in('test "first" do\nend\ndef test_second'), 'test_second')

    def test_shoulda_pattern_preserves_literal_symbols(self):
        self.assertEqual(plugin.TestMethodMatcher().find_first_match_in('should "a.b > c" do'), r'/a\.b\ >\ c/')

    def test_missing_test_reports_error_without_command(self):
        self.buffer('# no test here')
        self.assertIsNone(self.task.file_type().run_single_test_command(self.view))
        sublime.error_message.assert_called_once_with('No test name!')

    def test_windows_test_name_is_quoted_even_without_spaces(self):
        sublime.platform.return_value = 'windows'
        self.assertEqual(plugin.quote_argument('test_1_>_0'), '"test_1_>_0"')

    def test_unsaved_file_with_bundler_does_not_probe_environment(self):
        self.view.file_name.return_value = None
        self.settings['check_for_bundler'] = True
        with patch.object(plugin.os, 'popen') as popen:
            self.assertFalse(plugin.RunAllRubyTest(self.view).is_enabled())
            self.assertFalse(plugin.SwitchBetweenCodeAndTest(self.view).is_enabled(split_view=True))
            popen.assert_not_called()

    def test_bundler_uses_saved_working_directory_for_run_last(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'Gemfile').touch()
            self.settings['check_for_bundler'] = True
            self.view.file_name.return_value = None
            self.last_run.update(last_test_run='ruby test.rb', last_test_working_dir=root)
            command = plugin.RunLastRubyTest(self.view)
            command.display_results = Mock()
            command.run(None)
            options = self.window.run_command.call_args.args[1]
            self.assertEqual(options['working_dir'], root)
            self.assertEqual(options['shell_cmd'].strip(), 'bundle exec  ruby test.rb')

    def test_exec_uses_shell_cmd_on_modern_sublime_and_env(self):
        self.task.load_config()
        self.task.display_results = Mock()
        self.settings['env'] = {'RUBY_TEST_EXAMPLE': 'demo'}
        self.assertTrue(self.task.run_shell_command('ruby "test/example.rb"', str(ROOT)))
        options = self.window.run_command.call_args.args[1]
        self.assertEqual(options['shell_cmd'], 'ruby "test/example.rb"')
        self.assertNotIn('cmd', options)
        self.assertEqual(options['env'], {'RUBY_TEST_EXAMPLE': 'demo'})

    def test_legacy_sublime_exec_arguments(self):
        self.task.load_config()
        self.task.display_results = Mock()
        sublime.version.return_value = '2217'
        self.task.run_shell_command('ruby test.rb', str(ROOT))
        options = self.window.run_command.call_args.args[1]
        self.assertEqual(options['cmd'], ['ruby test.rb'])
        self.assertTrue(options['shell'])

    def test_missing_working_directory_does_not_start_process(self):
        self.assertFalse(self.task.run_shell_command('ruby test.rb', '/no/such/rubytest-folder'))
        self.window.run_command.assert_not_called()

    def test_spring_without_ruby_manager(self):
        self.settings['check_for_spring'] = True
        self.task.command_prefix(str(ROOT))
        self.assertEqual(plugin.COMMAND_PREFIX.strip(), 'spring')

    def test_cancel_uses_editor_process_tree_cancellation(self):
        plugin.CancelRubyTest(self.view).run(None)
        self.window.run_command.assert_called_once_with('exec', {'kill': True})

    def test_panel_toggle(self):
        command = plugin.ShowTestPanel(self.view)
        self.window.active_panel.return_value = 'output.exec'
        command.run(None)
        self.window.run_command.assert_called_with('hide_panel', {'panel': 'output.exec'})
        self.window.active_panel.return_value = None
        command.run(None)
        self.window.run_command.assert_called_with('show_panel', {'panel': 'output.exec'})

    def test_split_preserves_existing_horizontal_layout(self):
        self.window.num_groups.return_value = 2
        self.window.active_group.return_value = 0
        plugin.ShowPanels(self.window).split()
        self.window.run_command.assert_not_called()
        self.window.focus_group.assert_called_once_with(1)

    def test_new_horizontal_split(self):
        self.settings['split_orientation'] = 'horizontal'
        self.window.num_groups.return_value = 1
        plugin.ShowPanels(self.window).split()
        layout = self.window.run_command.call_args.args[1]
        self.assertEqual(layout['rows'], [0.0, 0.5, 1.0])

    def test_switch_uses_full_matching_directory_suffix(self):
        self.view.file_name.return_value = '/project/api/orders/get.rb'
        command = plugin.SwitchBetweenCodeAndTest(self.view)
        command.project_files = Mock(return_value=['/project/requests/api/admin/orders/get_spec.rb', '/project/requests/api/orders/get_spec.rb'])
        command.run(None)
        self.window.open_file.assert_called_once_with('/project/requests/api/orders/get_spec.rb')

    def test_switch_keeps_ambiguous_matches_for_user(self):
        self.view.file_name.return_value = '/project/app/models/item.rb'
        command = plugin.SwitchBetweenCodeAndTest(self.view)
        choices = ['/project/spec/models/item_spec.rb', '/project/test/models/item_test.rb']
        command.project_files = Mock(return_value=choices)
        command.run(None)
        self.window.open_file.assert_not_called()
        callback = self.window.show_quick_panel.call_args.args[1]
        callback(-1)
        self.window.open_file.assert_not_called()
        callback(1)
        self.window.open_file.assert_called_once_with(choices[1])

    def test_split_places_already_open_file_in_target_group(self):
        command = plugin.SwitchBetweenCodeAndTest(self.view)
        self.window.active_group.return_value = 1
        command.open_alternate('/project/item.rb', True)
        self.window.set_view_index.assert_called_once_with(self.window.open_file.return_value, 1, -1)

    def test_walk_prunes_ignored_directories(self):
        self.task.load_config()
        with tempfile.TemporaryDirectory() as root:
            for name in ('test/item_test.rb', 'vendor/item_test.rb', '.git/item_test.rb'):
                path = Path(root, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            self.window.folders.return_value = [root]
            command = plugin.SwitchBetweenCodeAndTest(self.view)
            self.assertEqual(command.project_files(lambda name: name == 'item_test.rb'), [str(Path(root, 'test/item_test.rb'))])

    def test_scratch_appends_through_editor_command(self):
        self.task.load_config()
        scratch = plugin.ShowInScratch(self.window)
        scratch.display_results()
        self.window.new_file.assert_called_once()
        self.window.new_file.return_value.set_name.assert_called_once_with('Test Results')
        scratch.append('1 run, 0 failures')
        scratch.view.run_command.assert_called_once_with('append', {'characters': '1 run, 0 failures', 'force': True, 'scroll_to_end': True})
        scratch.view.begin_edit.assert_not_called()

    def test_output_lookup_reuses_existing_panel(self):
        self.assertIs(plugin.output_panel(self.window), self.window.find_output_panel.return_value)
        self.window.get_output_panel.assert_not_called()

    def test_rerun_does_not_accumulate_after_callbacks(self):
        self.settings['after_callback'] = 'echo finished'
        self.task.load_config()
        self.task.display_results = Mock()
        self.task.run_shell_command('ruby test.rb', str(ROOT))
        self.assertEqual(self.last_run['last_test_run'], 'ruby test.rb')

    def test_project_suite_runs_from_open_root_when_source_is_nested(self):
        self.view.file_name.return_value = '/project/app/models/item.rb'
        command = plugin.RunRubyTestSuite(self.view)
        command.run_shell_command = Mock()
        command.run(None)
        command.run_shell_command.assert_called_once_with('rake test', '/project')

    def test_extract_variable_uses_command_edit_token(self):
        self.buffer('  puts 2 + 3')
        plugin.RubyReplaceWithVariable(self.view).run('edit-token', 7, 12, 'sum')
        self.view.replace.assert_called_once()
        self.assertEqual(self.view.replace.call_args.args[0], 'edit-token')
        self.view.insert.assert_called_once_with('edit-token', 0, '  sum = 2 + 3\n')

    def test_disabled_default_keybindings(self):
        self.settings['enable_keybindings'] = False
        listener = plugin.RubyTestKeybindings()
        self.assertFalse(listener.on_query_context(self.view, 'ruby_test_keybindings', sublime.OP_EQUAL, True, False))
        for path in ROOT.glob('*.sublime-keymap'):
            for binding in json.loads(re.sub(r'//[^\n]*', '', path.read_text())):
                self.assertIn({'key': 'ruby_test_keybindings', 'operator': 'equal', 'operand': True}, binding['context'])

    def test_generation_handles_test_word_in_project_name(self):
        self.task.load_config()
        self.view.file_name.return_value = '/ruby-tests-demo/app/models/exercise_test.rb'
        generator = plugin.GenerateTestFile(self.window, False)
        self.assertTrue(generator.is_valid_path('/ruby-tests-demo/spec/models'))
        self.assertEqual(generator.suggest_file_name('/ruby-tests-demo/spec/models'), 'exercise_test_spec.rb')

    def test_generation_keeps_test_prefix_when_switching_from_spec(self):
        self.task.load_config()
        self.view.file_name.return_value = '/project/spec/test_invoice_spec.rb'
        generator = plugin.GenerateTestFile(self.window, False)
        self.assertEqual(generator.suggest_file_name('/project/app/models'), 'test_invoice.rb')


if __name__ == '__main__':
    unittest.main()
