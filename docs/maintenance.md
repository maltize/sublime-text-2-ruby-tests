# Maintenance review — 2026-10-30

Reviewed all 55 open issues and their discussions. The changes focus on
reproducible plugin defects and concrete usage gaps. Original environments
that are unavailable are not treated as validated fixes.

## Resolved in this maintenance change

| Issue | Resolution |
| --- | --- |
| [#273](https://github.com/maltize/sublime-text-2-ruby-tests/issues/273) | Valid working directory and relative path for standalone tests. |
| [#272](https://github.com/maltize/sublime-text-2-ruby-tests/issues/272) | Syntax verification uses a path relative to the working directory. |
| [#269](https://github.com/maltize/sublime-text-2-ruby-tests/issues/269) | Documented Sublime Preferences `show_errors_inline: false`. |
| [#268](https://github.com/maltize/sublime-text-2-ruby-tests/issues/268) | Added Cancel Running Tests in palette and menus, delegating process-tree cancellation to exec. |
| [#267](https://github.com/maltize/sublime-text-2-ruby-tests/issues/267) | Updated Cucumber line selector syntax and documented environment arguments. |
| [#266](https://github.com/maltize/sublime-text-2-ruby-tests/issues/266) | Alternate files ranked by complete matching directory suffix. |
| [#265](https://github.com/maltize/sublime-text-2-ruby-tests/issues/265) | Added Run Project Test Suite, configurable for Rake or RSpec. |
| [#264](https://github.com/maltize/sublime-text-2-ruby-tests/issues/264) | Horizontal split setting; preserve existing group layouts. |
| [#261](https://github.com/maltize/sublime-text-2-ruby-tests/issues/261) | Added Scroll Output to Top command as a keyboard-accessible workaround. |
| [#258](https://github.com/maltize/sublime-text-2-ruby-tests/issues/258) | Exact basename detection with RSpec precedence. |
| [#247](https://github.com/maltize/sublime-text-2-ruby-tests/issues/247) | Added enable_keybindings setting and fixed User keymap menu paths. |
| [#246](https://github.com/maltize/sublime-text-2-ruby-tests/issues/246) | Select nearest declaration, support symbols, remove fixed 2,000-character limit. |
| [#243](https://github.com/maltize/sublime-text-2-ruby-tests/issues/243) | Treat Rails app files as code even when their name ends in _test.rb; generation uses folder boundaries. |
| [#240](https://github.com/maltize/sublime-text-2-ruby-tests/issues/240) | Initialize anonymous file state; defer environment detection until command execution. |
| [#236](https://github.com/maltize/sublime-text-2-ruby-tests/issues/236) | Added explicit env mapping and documented shell startup limitations. |
| [#232](https://github.com/maltize/sublime-text-2-ruby-tests/issues/232) | Standalone specs no longer produce a filename as cwd or a trailing slash. |
| [#228](https://github.com/maltize/sublime-text-2-ruby-tests/issues/228) | RSpec suffix takes precedence over test_ prefix. |
| [#221](https://github.com/maltize/sublime-text-2-ruby-tests/issues/221) | Show Test Panel now toggles visibility. |
| [#209](https://github.com/maltize/sublime-text-2-ruby-tests/issues/209) | Scratch uses a real scratch buffer and editor append command, with no begin_edit calls. |
| [#206](https://github.com/maltize/sublime-text-2-ruby-tests/issues/206) | Rerun uses saved cwd even from unsaved tabs with Bundler enabled. |
| [#200](https://github.com/maltize/sublime-text-2-ruby-tests/issues/200) | Configured test folders determine root independently of open-folder order. |
| [#191](https://github.com/maltize/sublime-text-2-ruby-tests/issues/191) | Added explicit env mapping and documented inherited-shell environments. |
| [#148](https://github.com/maltize/sublime-text-2-ruby-tests/issues/148) | Replaced deprecated edit calls in scratch output and variable extraction; actual editor checks pass. |
| [#76](https://github.com/maltize/sublime-text-2-ruby-tests/issues/76) | Split switching places an already-open file into the target group. |

## Kept open

| Issue | Reason / remaining work |
| --- | --- |
| [#270](https://github.com/maltize/sublime-text-2-ruby-tests/issues/270) | Announcement, no RubyTest defect or implementation request. |
| [#263](https://github.com/maltize/sublime-text-2-ruby-tests/issues/263) | Package-manager deletion report lacks reproduction; documented safe source-checkout installation. |
| [#262](https://github.com/maltize/sublime-text-2-ruby-tests/issues/262) | Image-only control-character report; likely related to #245, needs textual reproduction. |
| [#259](https://github.com/maltize/sublime-text-2-ruby-tests/issues/259) | Load-path guidance and real test_helper regression added; original environment not reproduced. |
| [#257](https://github.com/maltize/sublime-text-2-ruby-tests/issues/257) | Spork output redirection and detached-view traceback need a Spork reproduction. |
| [#255](https://github.com/maltize/sublime-text-2-ruby-tests/issues/255) | Installation docs updated; original native pg gem/dyld and PATH failures are environment-specific. |
| [#252](https://github.com/maltize/sublime-text-2-ruby-tests/issues/252) | Zeus/Bundler guidance updated; original legacy environment unavailable. |
| [#245](https://github.com/maltize/sublime-text-2-ruby-tests/issues/245) | ANSI terminal sequences are not interpreted; color-disable guidance added, full support remains open. |
| [#234](https://github.com/maltize/sublime-text-2-ruby-tests/issues/234) | Historical stale dummy-directory traceback; original settings and root-selection regression unavailable. |
| [#227](https://github.com/maltize/sublime-text-2-ruby-tests/issues/227) | Interactive terminal/Pry integration remains a separate feature. |
| [#223](https://github.com/maltize/sublime-text-2-ruby-tests/issues/223) | Documented underscore setting names and Gemfile root behavior; no reproduction of all reported bundle environments. |
| [#222](https://github.com/maltize/sublime-text-2-ruby-tests/issues/222) | Running matching tests directly from source remains a separate feature. |
| [#220](https://github.com/maltize/sublime-text-2-ruby-tests/issues/220) | ANSI rendering in arbitrary log files remains a separate feature. |
| [#219](https://github.com/maltize/sublime-text-2-ruby-tests/issues/219) | Modern shell_cmd routing and Windows real-shell checks added; original ST3 Windows editor environment unavailable. |
| [#217](https://github.com/maltize/sublime-text-2-ruby-tests/issues/217) | Documented file:line syntax; original Zeus/RSpec environment unavailable. |
| [#216](https://github.com/maltize/sublime-text-2-ruby-tests/issues/216) | RSpec HTML report integration remains a separate feature. |
| [#208](https://github.com/maltize/sublime-text-2-ruby-tests/issues/208) | Failure diagnostics come from Sublime exec and RSpec; no filtering feature added. |
| [#192](https://github.com/maltize/sublime-text-2-ruby-tests/issues/192) | Sublime Text 2 native crash cannot be validated with the installed editor. |
| [#190](https://github.com/maltize/sublime-text-2-ruby-tests/issues/190) | One comment shares the standalone-path cause and is fixed; generic no-output reports need reproduction. |
| [#188](https://github.com/maltize/sublime-text-2-ruby-tests/issues/188) | chruby support is already merged; not validated with a local chruby installation. |
| [#187](https://github.com/maltize/sublime-text-2-ruby-tests/issues/187) | RVM/rspec executable selection requires the original environment. |
| [#184](https://github.com/maltize/sublime-text-2-ruby-tests/issues/184) | Root handling corrected and documented; no Cucumber step-discovery environment available for validation. |
| [#178](https://github.com/maltize/sublime-text-2-ruby-tests/issues/178) | Root handling and helper-load guidance improved; original RVM/RSpec environment unavailable. |
| [#162](https://github.com/maltize/sublime-text-2-ruby-tests/issues/162) | Filename rules and unsaved-view crashes addressed; intermittent legacy menu disablement not reproduced. |
| [#157](https://github.com/maltize/sublime-text-2-ruby-tests/issues/157) | Bundler auto-detection already exists; documented and covered by regression tests. |
| [#154](https://github.com/maltize/sublime-text-2-ruby-tests/issues/154) | Existing rbenv detection handles Homebrew/PATH; original shell-function environment not reproduced. |
| [#146](https://github.com/maltize/sublime-text-2-ruby-tests/issues/146) | ruby_noexec_wrapper failure belongs to the Ruby/RVM environment; launch/PATH guidance added. |
| [#118](https://github.com/maltize/sublime-text-2-ruby-tests/issues/118) | Zeus examples updated; original ST2/Zeus freeze not reproduced. |
| [#116](https://github.com/maltize/sublime-text-2-ruby-tests/issues/116) | Historical Sublime core Unicode environment bug; no local ST2 build for validation. |
| [#108](https://github.com/maltize/sublime-text-2-ruby-tests/issues/108) | Shoulda pattern matching tested; Ruby 1.8.7/Test::Unit process behavior not reproduced. |
| [#64](https://github.com/maltize/sublime-text-2-ruby-tests/issues/64) | Single Minitest::Spec it-block selection remains unsupported; documented explicitly. |

See [validation](validation.md) for evidence and platform limits. New controls use
Sublime’s existing build process and panel APIs. Refactoring is limited to path
handling, nearest-test selection, and edits requiring a TextCommand edit token.
