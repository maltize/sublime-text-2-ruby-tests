# Review of the four remaining pull requests

Reviewed against the maintained code on 2026-10-30. The old branches are not
merged wholesale: useful behavior is applied to the current implementation,
with regression coverage and the original contributors credited.

| PR | Decision | Implementation / evidence |
| --- | --- | --- |
| [#260](https://github.com/maltize/sublime-text-2-ruby-tests/pull/260) — Bundler/Spring order | Adopted | Compose manager → `bundle exec` → `spring` → runner. A Bash integration check executes the resulting chain through executable stand-ins and verifies the order. The unrelated metadata edit is omitted. |
| [#250](https://github.com/maltize/sublime-text-2-ruby-tests/pull/250) — system Ruby managers | Adapted | Search executable files on PATH, then known user/system locations, including system RVM and Apple Silicon Homebrew. Honor `rvm_path`. Avoid shell `which`, validate executability, and quote the selected path. Preserve the direct-Ruby RVM correction. |
| [#251](https://github.com/maltize/sublime-text-2-ruby-tests/pull/251) — `internal_dir` | Superseded | Existing root selection runs `analyzer/spec/lib/item_spec.rb` from `analyzer`, with `spec/lib/item_spec.rb` as its argument. A regression covers that exact project shape. No command-wide regex replacement or extra setting is needed. |
| [#225](https://github.com/maltize/sublime-text-2-ruby-tests/pull/225) — experimental chruby | Superseded and hardened | chruby support was already merged separately. The old PR checks a shell command string as an executable path. Current handling locates the initialization script, supports Homebrew locations, reads each project's `.ruby-version`, and keeps the current Ruby when that file is absent. It never starts a bare `ruby` as a fallback. |

chruby shell-composition checks cover no version file, separate project versions,
and an unavailable version preventing test execution. They use an initialization
script stand-in; they are not a claim of testing every chruby installation.
RVM is additionally exercised with the real local installation in Sublime.
