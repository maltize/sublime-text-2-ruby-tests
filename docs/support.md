# Support and scope

The maintained target is Sublime Text 3/4 with a Ruby and test framework that
work together from the project's terminal environment. Current validation uses
Sublime Text 4 build 4215 on macOS, Ruby 3.4 in CI, and Ruby 4.0.5 locally.
See [validation](validation.md) for exact coverage and platform limits.

Sublime Text 2, historical Ruby 1.8/1.9 environments, and old Zeus/Spork server
integrations are no longer maintained. Existing compatibility code or custom
command examples may remain, but they do not imply support for those setups.
Historical reports are closed as not planned rather than marked as fixed.

RubyTest focuses on running saved test files or selected tests, showing their
text output, and switching between source and test files. The following feature
requests were reviewed and declined during the 2026-10-30 maintenance session:

- Selecting individual Minitest::Spec `it` blocks (#64). Whole-file execution
  remains available with an appropriate command and filename convention.
- Automatically resolving and running a test file from the source buffer
  (#222). Switch to the test, run the project suite, or rerun the last test.
- A terminal emulator or interactive Pry/debugger integration (#227).
- Embedded RSpec HTML reports (#216).
- ANSI interpretation/removal or rendering arbitrary log files (#245, #262,
  #220). Configure plain output in the framework or use an appropriate viewer.
- Filtering Sublime build diagnostics or framework summaries (#208).

New reproducible defects on maintained configurations are welcome. Include the
Sublime build, OS, Ruby/framework versions, filename, working directory, command
templates, and full console traceback. An old report can be revisited with a
current reproduction; its closure is not a claim that every symptom was fixed.
