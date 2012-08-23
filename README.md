Sublime Text 2 Ruby Tests
=========================

Overview
--------
Running:

  - ruby unit tests (all tests from file / single test)
  - cucumber tests (feature / scenario)
  - rspec (full spec, single spec)

Maintainers:
------------
* Maciej Gajek (https://github.com/maltize)
* Grzegorz Smajdor (https://github.com/gs)
* Tejas Dinkar (https://github.com/gja)

Installation
------------

Go to your Sublime Text 2 `Packages` directory

 - OS X: `~/Library/Application\ Support/Sublime\ Text\ 2/Packages`
 - Windows: `%APPDATA%/Sublime Text 2/Packages/`
 - Linux: `~/.config/sublime-text-2/Packages/`

and clone the repository using the command below:

``` shell
git clone https://github.com/maltize/sublime-text-2-ruby-tests.git RubyTest
```

Settings
--------

You can specify different binary for each type of test to use.

Make a copy of `RubyTest.sublime-settings` file to `~/Library/Application Support/Sublime Text 2/Packages/User/` and make your changes.


Usage
-----

 - Run single ruby test: `Command-Shift-R`
 - Run all ruby tests from current file: `Command-Shift-T`
 - Run last ruby test(s): `Command-Shift-E`
 - Show test panel: `Command-Shift-X` (when test panel visible hit `esc` to hide it)
 - Check RB, ERB file syntax: `Alt-Shift-V`
 - Switching between code and test:
    - Single View: `Command-`.
    - Split View:  `Command+Ctrl+`.
Keys:
 'Command' (OSX)
 'Ctrl' (Linux / Windows)

 ![ruby_tests screenshot](https://github.com/maltize/sublime-text-2-ruby-tests/raw/master/ruby_tests.png)


Additional Features:
-------------------
Below features can be enabled by editing `RubyTest.sublime-settings`

- Save on Run - if enabled then files will be automatically saved when running the test
  `"save_on_run": true`

- Use Scratch  - test output in new tab
 `"ruby_use_scratch" : true `

Colors Issue:
------------
We have known colors issue. Please check [this thread](https://github.com/maltize/sublime-text-2-ruby-tests/issues/33#issuecomment-3553701) for temporary solution.

Note
----
Before reporting an issue be sure to :

  - Run Sublime Text 2 from [command line](http://www.sublimetext.com/docs/2/osx_command_line.html)

If this will not help provide to us debug informations using (CTRL + ` )

Please open an issue at https://github.com/maltize/sublime-text-2-ruby-tests if you discover a problem or would like to see a feature/change implemented.


Settings:
---------

    {
      "erb_verify_command": "erb -xT - {file_name} | ruby -c",
      "ruby_verify_command": "ruby -c {file_name}",

      "run_ruby_unit_command": "ruby -Itest {relative_path}",
      "run_single_ruby_unit_command": "ruby -Itest {relative_path} -n '{test_name}'",

      "run_cucumber_command": "cucumber {relative_path}",
      "run_single_cucumber_command": "cucumber {relative_path} -l{line_number}",

      "run_rspec_command": "rspec {relative_path}",
      "run_single_rspec_command": "rspec {relative_path} -l{line_number}",

      "ruby_unit_folder": "test",
      "ruby_cucumber_folder": "features",
      "ruby_rspec_folder": "spec",

      "ruby_use_scratch" : false,
      "save_on_run": false,
      "ignored_directories": [".git", "vendor", "tmp"] 
    }

Bundler support:
----------------
First be sure that you have your copy of `RubyTest.sublime-settings` placed in User folder (refer to Settings above) and replace each prefix each command with "bundle exec". ex:

    "run_rspec_command": "bundle exec rspec {relative_path}"


Spin support:
-------------

First be sure that you have your copy of `RubyTest.sublime-settings` placed in User folder (refer to Settings above) and replace the following settings. ex:

    {
      "erb_verify_command": "erb -xT - {file_name} | ruby -c",
      "ruby_verify_command": "ruby -c {file_name}",

      "run_ruby_unit_command": "spin push -Itest {relative_path}",
      "run_single_ruby_unit_command": "ruby -Itest {relative_path} -n '{test_name}'",

      "run_cucumber_command": "cucumber {relative_path}",
      "run_single_cucumber_command": "cucumber {relative_path} -l{line_number}",

      "run_rspec_command": "spin push {relative_path}",
      "run_single_rspec_command": "spin push {relative_path} -l{line_number}",

      "ruby_unit_folder": "test",
      "ruby_cucumber_folder": "features",
      "ruby_rspec_folder": "spec",

      "ruby_use_scratch" : false,
      "save_on_run": false,
      "ignored_directories": [".git", "vendor", "tmp"] 
    }
