# RubyTest for Sublime Text

Run Ruby Test::Unit/Minitest tests, RSpec examples, and Cucumber scenarios from
Sublime Text, and switch between source and test files. Targets Sublime Text
3 and 4. Editor validation currently covers Sublime Text 4; the legacy Sublime
Text 2 execution path is retained. See [validation](docs/validation.md) for
tested versions and limitations.

## Installation and development

Install **RubyTest** through Package Control. Ruby and the test framework must
already be installed and runnable in your project's environment.

For a source checkout, choose **Preferences → Browse Packages…** and clone into
that exact directory:

```sh
git clone https://github.com/maltize/sublime-text-2-ruby-tests.git RubyTest
```

The directory must be named `RubyTest`. An unpacked `Packages/RubyTest` checkout
overrides `Installed Packages/RubyTest.sublime-package`, so you can keep the
Package Control installation while developing. Restart Sublime after adding the
checkout. To return to the packaged version, move the checkout outside Packages.
Keep a development checkout outside Packages and symlink it there if you want to
protect it from package-management changes. Do not edit the installed archive.

## Running tests

Open your project folder, save the test file, and use the Command Palette
(`RubyTest:`) or **Tools → RubyTest**. Default shortcuts are:

| Action | macOS | Windows / Linux |
| --- | --- | --- |
| Run single test at caret | Command+Shift+R | Ctrl+Shift+R |
| Run all tests in current file | Command+Shift+T | Ctrl+Shift+T |
| Rerun last command | Command+Shift+E | Ctrl+Shift+E |
| Toggle test panel | Command+Shift+X | Ctrl+Shift+X |
| Verify Ruby / ERB syntax | Alt+Shift+V | Alt+Shift+V |
| Switch code ↔ test | Command+. | Ctrl+. |
| Switch code ↔ test in split view | Command+Ctrl+. | Ctrl+Shift+. |
| Create file | Command+Shift+C | Ctrl+Shift+C |

**Run All Ruby Tests** runs the current file. **Run Project Test Suite** runs
`rake test` in the test's project root; use `"check_for_bundler": true` to prepend
`bundle exec` when that directory has a Gemfile. For an RSpec suite, set
`"run_ruby_suite_command": "rspec spec"`. These commands also appear in the
Command Palette; the suite command has no default shortcut.

**Cancel Running Tests** is available in the Command Palette, Tools menu, and
right-click RubyTest menu. It delegates to Sublime's build cancellation, including
process-tree termination on Windows. Escape hides a panel; it does not stop tests.
The `exec` panel is shared with other builds, so cancellation stops its current
process. **Scroll Output to Top** returns to the start of the output without a mouse.

Single-test detection supports `def test_name`, Rails-style `test "name" do`, and
Shoulda `should "name" do`. Put the caret on the declaration or inside its body.
Minitest::Spec's `it` blocks are not yet supported for single-test selection.
RSpec and Cucumber use the caret's line number. Save changes before running, or
enable `"save_on_run": true`; syntax verification checks the saved file.

## Test names, paths, and switching

Detection uses the filename, with `_spec.rb` taking precedence over `test_`:

- `item_spec.rb`, `test_item_spec.rb`, `splittest_spec.rb`: RSpec.
- `item_test.rb`, `test_item.rb`: Test::Unit / Minitest.
- `item.feature`: Cucumber.
- `app/models/exercise_test.rb`: application code; its spec can be
  `spec/models/exercise_test_spec.rb`.

A test under `test/`, `spec/`, or `features/` runs from the directory immediately
above that configured folder. For example, `shop/spec/models/item_spec.rb` runs
from `shop`, even if the whole monorepo or `shop/spec` is open in Sublime.
Customize these folder names with `ruby_unit_folder`, `ruby_rspec_folder`, and
`ruby_cucumber_folder`. A test outside those folders uses the deepest containing
open project folder, or its own directory when no project folder contains it.
The path passed to the runner is relative to that working directory. Syntax
verification uses the same relative path, so nested tests work too.

Switching searches open folders and skips `ignored_directories`. For duplicate
basenames it prefers the longest matching directory suffix. For example,
`api/orders/get.rb` prefers `requests/api/orders/get_spec.rb` over
`requests/api/admin/orders/get_spec.rb`. Equal matches appear in a chooser.
If no file exists, RubyTest offers to create one. Switching needs an open project
folder to search.

Split switching preserves an existing layout and opens the other file in the next
group. With one group, it creates a vertical split; set
`"split_orientation": "horizontal"` for source above test.

## Settings

Choose **Preferences → Package Settings → RubyTest → Settings – User**. Add only
the settings you want to override in `Packages/User/RubyTest.sublime-settings`.
The complete defaults are in [RubyTest.sublime-settings](RubyTest.sublime-settings).
If you copied the entire defaults file in the past, your old commands still take
precedence: remove unwanted overrides to receive updated commands and quoting.

For example:

```json
{
  "check_for_bundler": true,
  "save_on_run": true,
  "split_orientation": "horizontal",
  "ruby_use_scratch": false,
  "env": {"RAILS_ENV": "test", "PGHOST": "localhost"}
}
```

`ruby_use_scratch` puts output in a read-only scratch tab. The output panel is
still available. Scratch copying currently stops after one minute.
`hide_panel` hides the output panel after starting a command. `terminal_encoding`
defaults to `utf-8`; on Windows use `chcp` to identify another encoding if needed
(for example, `cp936`). `before_callback` and `after_callback` run shell commands
around the test invocation.

Command templates accept `{relative_path}` and, for single RSpec/Cucumber runs,
`{line_number}`. Unit-test templates also accept `{test_name}` (raw name) and
`{test_name_quoted}` (quoted for the platform shell). Syntax commands use
`{file_name}`, which is relative to the working directory and can include folders.
Quote path placeholders in custom commands, especially for spaces:

```json
{
  "run_ruby_unit_command": "ruby -Itest \"{relative_path}\"",
  "run_single_ruby_unit_command": "ruby -Itest \"{relative_path}\" -n {test_name_quoted}",
  "run_rspec_command": "rspec \"{relative_path}\"",
  "run_single_rspec_command": "rspec \"{relative_path}:{line_number}\"",
  "run_single_cucumber_command": "cucumber \"{relative_path}:{line_number}\" ENVIRONMENT=LOCAL BROWSER=true --format pretty"
}
```

Attach Cucumber's line number to the file path, before environment assignments;
replace old `-l{line_number}` templates with the example above. Commands can also
be overridden through view/project settings, using the same setting names.

### Ruby versions, Bundler, Spring, and Zeus

RubyTest inherits Sublime's environment. If Ruby, gems, or environment variables
are missing, verify the command from the same project root in a terminal, then
launch Sublime from that environment with `subl .`. Set explicit variables using
RubyTest's `env` mapping (or project `build_env` settings). Shell startup files
are not all loaded by editor builds; a variable in an interactive `.bashrc` is
not automatically available. Keep private values in User settings, outside Git.

The opt-in settings are `check_for_chruby`, `check_for_rbenv`, `check_for_rvm`,
`check_for_bundler`, and `check_for_spring` — use underscores, not hyphens.
Bundler checks the working directory's Gemfile. Do not also put `bundle exec`
in templates when automatic Bundler support is enabled. Ruby managers can also
be initialized through your shell's PATH; detection is optional.

For RVM, enable `"check_for_rvm": true` and leave the command templates starting
with `ruby`, `rspec`, or `cucumber`. RubyTest adds the RVM wrapper automatically.
For example:

```json
{
  "check_for_rvm": true,
  "check_for_bundler": true
}
```

An error pointing at `.../bin/ruby:1` with bytes such as `0xCF`, `0xFA`, `0xED`,
and `0xFE` means Ruby was asked to parse its own native executable. Older
RubyTest versions constructed `rvm-auto-ruby -S ruby ...` for unit tests and
syntax checks. The plugin now calls `rvm-auto-ruby ...` directly for those
commands, while keeping `-S` for Ruby scripts such as `rspec`, `rake`, or `bundle`.
Do not add an RVM wrapper to custom templates as well as enabling auto-detection.

For Zeus, start `zeus start` in a terminal, then use:

```json
{
  "check_for_bundler": false,
  "run_rspec_command": "zeus rspec \"{relative_path}\"",
  "run_single_rspec_command": "zeus rspec \"{relative_path}:{line_number}\"",
  "run_cucumber_command": "zeus cucumber \"{relative_path}\" --no-color",
  "run_single_cucumber_command": "zeus cucumber \"{relative_path}:{line_number}\" --no-color"
}
```

Enable Bundler only if Zeus is part of that bundle. A `bundler: command not found:
zeus` message means the selected bundle does not provide the executable. Spin can
be used similarly by setting `run_rspec_command` to `spin push "{relative_path}"`
and its single-test variant to `spin push "{relative_path}:{line_number}"`.

### Shortcuts and output

To disable all RubyTest default shortcuts, set `"enable_keybindings": false` in
RubyTest settings. Add your preferred bindings in **Preferences → Key Bindings**:

```json
[
  {"keys": ["super+shift+y"], "command": "run_all_ruby_test"}
]
```

Use `ctrl+shift+y` on Windows/Linux. Disabling defaults releases
Command/Ctrl+Shift+T for reopening tabs and Command+Shift+R for Sublime's symbol
navigation. Adding a new binding alone does not remove the old one.

To disable backtrace annotations, put `"show_errors_inline": false` in Sublime's
**Preferences → Settings**, rather than RubyTest settings. This is Sublime's
build-output preference and applies to other builds too.

The TestConsole syntax colors plain test output; it does not interpret terminal
ANSI sequences. Prefer `--no-color` in RSpec/Cucumber commands and disable color
in other reporters. Interactive debuggers such as Pry require a terminal; the
normal RubyTest output panel does not provide terminal input.

## Try the demo

Install Minitest and Rake if your Ruby does not already provide them, then open
[examples/demo.sublime-project](examples/demo.sublime-project) in Sublime.

From the repository root, first check that the selected Ruby can run the demo:

```sh
ruby --version
gem install minitest rake --no-document
cd examples
ruby -Itest standalone_test.rb -n test_add
rake test
```

The standalone command should report one passing test; Rake should report two.
If these terminal commands fail, check your selected Ruby and gems before
running them in the editor. With RVM, select your project Ruby using `rvm use`
before installing the gems.

1. Open `examples/calculator.rb` and switch to its test with Command/Ctrl+period.
2. Put the caret in `test 'sum > 0'` and run **RubyTest: Run Single Test**: one test passes.
3. Run **Run All Ruby Tests**: both tests pass.
4. Verify syntax in that nested test file: `Syntax OK`.
5. Open `standalone_test.rb` and run its single test from the project root.
6. Use **Run Project Test Suite** to run the demo's Rake test task.

See [editor validation](docs/validation.md) for repeatable smoke checks and
[the maintenance review](docs/maintenance.md) for issue scope and remaining work.

## Development

```sh
python3 -W error -m unittest discover -s tests -v
```

The tests compile source directly so cached bytecode cannot hide invalid escape
warnings. CI runs Python 3.8, 3.12, and 3.14 on Ubuntu 22.04, plus Windows command
execution checks. Editor checks complement the API doubles.

Maintainers: [Maciej Gajek](https://github.com/maltize),
[Grzegorz Smajdor](https://github.com/gs), [Tejas Dinkar](https://github.com/gja).
Please include the Sublime build, OS, Ruby/framework versions, filename, working
directory, custom commands, and console traceback when reporting a problem.

## Support

Bitcoin: 1KBqcRsfmdh8rGV9Mx6sJmYuB6y517BZHy

PayPal: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=TSRXZ54B8WDEN&lc=US&item_name=Sublime%20Text%202%20Ruby%20Tests%20Plugin&item_number=RubyTest%20Plugin&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted)
