# Validation

Validated on 2026-10-30 with Sublime Text build 4215 on macOS, using the checkout
as `Packages/RubyTest` alongside the Package Control archive. Existing User
settings were temporarily overridden in memory and restored after each run.
Ruby 4.0.5 and Minitest 6.0.6 ran the demo tests.

## Automated regression checks

```sh
python3 -W error -m unittest discover -s tests -v
```

44 checks cover detection, standalone and nested paths, Windows separators and
drives, literal folder names, duplicate filenames, test selection, command
routing, Bundler reruns, panels, splits, scratch buffers, and editor edit tokens.
Four checks run generated commands through the real shell and Ruby, including
paths containing spaces, `test_helper` loading, and a test name containing `>`.
Ruby and Minitest are required for those four; install Minitest if necessary.
They are skipped only when the Ruby executable is absent.

The source-compilation test reads and compiles `run_ruby_test.py` directly under
`warnings.simplefilter('error')`, so `.pyc` files cannot hide invalid escapes.
The suite passes locally on Python 3.12, 3.13, and 3.14. CI uses Ubuntu 22.04 for
Python 3.8, 3.12, and 3.14, and Windows 2022 / Python 3.12 for the four real-shell
checks. All CI jobs install Ruby 3.4 and Minitest.

## Actual editor checks

Open a dedicated window for `examples/demo.sublime-project`. From Sublime's
console (View → Show Console), run the following with your checkout's absolute
path substituted:

```python
import runpy; smoke = runpy.run_path('/absolute/path/to/RubyTest/tests/editor_smoke.py'); smoke['run']('/absolute/path/to/RubyTest')
```

The script reloads the plugin, waits for command registration, and exercises
real editor commands. It temporarily uses the repository defaults and restores
the previous values and last-run settings. It changes only the dedicated demo
window's project/layout and opens demo or scratch buffers. Do not run it in a
window with valuable unsaved project state.

All 13 checks passed:

- Syntax verification on a nested test: `Syntax OK`.
- A single Rails-style test containing `>`: one test, zero failures.
- All tests in a nested file: two tests, zero failures.
- A standalone root test: one test, zero failures.
- Rerun from an unsaved tab with Bundler enabled: one test, zero failures.
- Scratch output contains the actual test results.
- Variable extraction edits the buffer through a TextCommand edit token.
- Switching source → test → source opens the expected files.
- Horizontal split creation and subsequent switching preserve the layout.
- Panel visibility toggles and Scroll Output to Top resets its viewport.
- The default Rake project suite runs from a source file.
- An explicit environment variable reaches the Ruby process.
- A long-running suite prints its start marker and ends with `[Cancelled]`.

Results are written to `rubytest-editor-results.json` in Python's temporary
directory. [Recorded results](editor-results.json) are included. The script uses
explicit exceptions because Sublime's optimized Python host can disable `assert`
statements.

The editor checks ran on macOS. Windows command quoting is exercised in CI;
Windows editor cancellation delegates to Sublime's native process-tree handling
and has not been tested in a Windows GUI here. Sublime Text 2's old execution
arguments have a regression check, but no native ST2 run. RSpec/Cucumber command
construction is tested; the historic Zeus, Spork, Ruby 1.8.7, and native-gem
setups in older issues were not recreated.
