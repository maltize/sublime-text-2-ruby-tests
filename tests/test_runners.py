"""Exercise runner composition in Bash with small executable stand-ins."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import test_ruby_test as fixtures


@unittest.skipUnless(os.name != 'nt' and shutil.which('bash') and shutil.which('ruby'),
                     'Bash runner integration requires a Unix Ruby environment')
class RunnerIntegration(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.PluginTests()
        fixture.setUp()
        self.settings, self.task = fixture.settings, fixture.task
        self.window = fixture.window
        self.temporary = tempfile.TemporaryDirectory(prefix='rubytest runners ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.trace = self.root / 'trace'
        self.task.display_results = Mock()

    def execute(self, command, directory, env=None, expected_returncode=0):
        result = subprocess.run(['bash', '-c', command], cwd=directory, env=env,
                                input='', text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=10)
        self.assertEqual(result.returncode, expected_returncode, result.stdout)
        return result.stdout

    def test_rvm_bundle_spring_then_ruby(self):
        binaries = self.root / 'bin'
        binaries.mkdir()
        scripts = {
            'rvm-auto-ruby': '#!/usr/bin/env bash\nprintf "rvm\\n" >> "$TRACE"\nexec ruby "$@"\n',
            'bundle': '#!/usr/bin/env ruby\nFile.open(ENV.fetch("TRACE"), "a") { |f| f.puts "bundle" }; abort unless ARGV.shift == "exec"; exec(*ARGV)\n',
            'spring': '#!/usr/bin/env ruby\nFile.open(ENV.fetch("TRACE"), "a") { |f| f.puts "spring" }; exec(*ARGV)\n',
        }
        for name, contents in scripts.items():
            path = binaries / name
            path.write_text(contents)
            path.chmod(0o755)
        (self.root / 'Gemfile').touch()
        self.settings.update(check_for_rvm=True, check_for_bundler=True, check_for_spring=True)
        self.task.load_config()
        env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH'], TRACE=str(self.trace))
        with patch.dict(os.environ, env):
            self.task.run_shell_command("ruby -e 'puts :runner_ok'", str(self.root))
        command = self.window.run_command.call_args.args[1]['shell_cmd']
        self.assertEqual(self.execute(command, self.root, env).strip(), 'runner_ok')
        self.assertEqual(self.trace.read_text().splitlines(), ['rvm', 'bundle', 'spring'])

    def chruby_command(self, directory):
        script = self.root / 'chruby script.sh'
        script.write_text('''chruby() {
  [ "$1" != missing ] || return 1
  printf '%s\\n' "$1" >> "$TRACE"
  export RUBYTEST_SELECTED="$1"
}
''')
        self.settings['check_for_chruby'] = True
        self.task.load_config()
        with patch.object(self.task, 'chruby_script', return_value=str(script)):
            self.task.run_shell_command('ruby -e \'puts ENV.fetch("RUBYTEST_SELECTED", "system")\'', str(directory))
        return self.window.run_command.call_args.args[1]['shell_cmd']

    def test_chruby_without_version_keeps_current_ruby(self):
        command = self.chruby_command(self.root)
        env = dict(os.environ, TRACE=str(self.trace))
        env.pop('RUBYTEST_SELECTED', None)
        self.assertEqual(self.execute(command, self.root, env).strip(), 'system')
        self.assertFalse(self.trace.exists())

    def test_chruby_reads_each_projects_version_in_its_working_directory(self):
        env = dict(os.environ, TRACE=str(self.trace))
        for version in ('ruby-one', 'ruby-two'):
            project = self.root / version
            project.mkdir()
            (project / '.ruby-version').write_text(version + '\n')
            command = self.chruby_command(project)
            self.assertEqual(self.execute(command, project, env).strip(), version)
        self.assertEqual(self.trace.read_text().splitlines(), ['ruby-one', 'ruby-two'])

    def test_chruby_missing_version_fails_without_running_test(self):
        (self.root / '.ruby-version').write_text('missing\n')
        command = self.chruby_command(self.root)
        output = self.execute(command, self.root, dict(os.environ, TRACE=str(self.trace)), expected_returncode=1)
        self.assertEqual(output, '')
