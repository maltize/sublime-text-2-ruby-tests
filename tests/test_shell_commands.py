"""Execute generated commands through the real platform shell and Ruby."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import test_ruby_test as fixtures


@unittest.skipUnless(shutil.which('ruby'), 'Ruby is required for shell integration checks')
class ShellCommands(unittest.TestCase):
    def setUp(self):
        # Reuse only the editor fixture, not its platform-specific path assertions.
        self.fixture = fixtures.PluginTests()
        self.fixture.setUp()
        self.task, self.window, self.view = self.fixture.task, self.fixture.window, self.fixture.view
        self.temporary = tempfile.TemporaryDirectory(prefix='rubytest space ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.window.folders.return_value = [str(self.root)]
        fixtures.sublime.platform.return_value = 'windows' if os.name == 'nt' else 'osx'
        (self.root / 'test').mkdir()
        (self.root / 'test' / 'test_helper.rb').write_text('HELPER_LOADED = true\n')
        self.test_file = self.root / 'test' / 'calculator space_test.rb'
        self.test_file.write_text('''require 'test_helper'
require 'minitest/autorun'
class CalculatorTest < Minitest::Test
  def test_first
    assert HELPER_LOADED
  end
  define_method('test_sum_>_0') { assert_equal 5, 2 + 3 }
end
''')

    def run_command(self, command, directory):
        result = subprocess.run(command, shell=True, cwd=directory, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout)
        return result.stdout

    def test_nested_syntax_with_spaces(self):
        file = self.task.file_type(str(self.test_file))
        self.assertIn('Syntax OK', self.run_command(file.verify_syntax_command(), file.get_project_root()))

    def test_unit_runner_loads_test_helper_from_project_root(self):
        file = self.task.file_type(str(self.test_file.with_name('calculator_test.rb')))
        self.test_file.rename(file.absolute_path)
        output = self.run_command(file.run_all_tests_command(), file.get_project_root())
        self.assertRegex(output, r'2 runs, [0-9]+ assertions, 0 failures')

    def test_selected_test_with_shell_redirection_symbol(self):
        # The view DSL matches the generated Ruby method above.
        path = self.test_file.with_name('calculator_test.rb')
        self.test_file.rename(path)
        self.view.file_name.return_value = str(path)
        self.fixture.buffer('test "sum > 0" do\n  assert_equal 5, 2 + 3\nend')
        file = self.task.file_type(str(path))
        output = self.run_command(file.run_single_test_command(self.view), file.get_project_root())
        self.assertRegex(output, r'1 runs, [0-9]+ assertions, 0 failures')
        self.assertFalse((self.root / '0').exists(), 'The shell interpreted > as redirection')

    def test_standalone_test_runs_without_test_folder(self):
        path = self.root / 'standalone_test.rb'
        path.write_text("require 'minitest/autorun'\nclass StandaloneTest < Minitest::Test\n  def test_ok\n    assert true\n  end\nend\n")
        self.window.folders.return_value = []
        file = self.task.file_type(str(path))
        output = self.run_command(file.run_all_tests_command(), file.get_project_root())
        self.assertRegex(output, r'1 runs, [0-9]+ assertions, 0 failures')
