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

Donate - support us!
--------------------

Bitcoin: 1KBqcRsfmdh8rGV9Mx6sJmYuB6y517BZHy

PayPal: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=TSRXZ54B8WDEN&lc=US&item_name=Sublime%20Text%202%20Ruby%20Tests%20Plugin&item_number=RubyTest%20Plugin&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted)

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

'Sublime Text 2' -> 'Preferences' -> 'Package Settings' -> 'RubyTest'

Make a copy of `RubyTest.sublime-settings` file to `~/Library/Application\ Support/Sublime\ Text\ 2/Packages/User/` and make your changes.


Usage
-----

 - Run single ruby test: `Command-Shift-R`
 - Run all ruby tests from current file: `Command-Shift-T`
 - Run last ruby test(s): `Command-Shift-E`
 - Show test panel: `Command-Shift-X` (when test panel visible hit `esc` to hide it)
 - Check RB, ERB file syntax: `Alt-Shift-V`
 - Switching between code and test (create a file if not found):
    - Single View: `Command-.`
    - Split View:  `Command-Ctrl-.`
 - Easy file creation: `Command-Shift-C`
Keys:
 'Command' (OSX)
 'Ctrl' (Linux / Windows)

 ![ruby_tests screenshot](https://github.com/maltize/sublime-text-2-ruby-tests/raw/master/ruby_tests.png)


Additional Features:
-------------------
Below features can be enabled by editing `RubyTest.sublime-settings`

- RVM / RBENV auto detect (thx to @bronson) - feature is disabled by default, but if you enable it then be sure that your settings file is configure to use `bundle exec` (refer to https://github.com/maltize/sublime-text-2-ruby-tests#bundler-support)
  `"check_for_rbenv": true`
  `"check_for_rvm": true`

- Save on Run - if enabled then all files will be automatically saved before running the test
  `"save_on_run": true`

- Use Scratch  - test output in new tab
 `"ruby_use_scratch" : true `

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
  
      "check_for_rbenv": false,
      "check_for_rvm": false,
      "check_for_bundler": false,
      "check_for_spring": false,
  
      "ruby_use_scratch" : false,
      "save_on_run": false,
      "ignored_directories": [".git", "vendor", "tmp"],
  
      "hide_panel": false,
  
      "before_callback": "",
      "after_callback": "",
  
      "theme": "Packages/RubyTest/TestConsole.hidden-tmTheme",
      "syntax": "Packages/RubyTest/TestConsole.tmLanguage"
    }

Bundler support:
----------------

There is a bundler autodetect feature - based on presence of `Gemfile` in projects root directory. Use `"check_for_bundler": true` settings for it.

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
      "run_single_rspec_command": "spin push {relative_path}:{line_number}",

      "ruby_unit_folder": "test",
      "ruby_cucumber_folder": "features",
      "ruby_rspec_folder": "spec",

      "ruby_use_scratch" : false,
      "save_on_run": false,
      "ignored_directories": [".git", "vendor", "tmp"],

      "hide_panel": false,

      "before_callback": "",
      "after_callback": "",

      "theme": "Packages/RubyTest/TestConsole.hidden-tmTheme",
      "syntax": "Packages/RubyTest/TestConsole.tmLanguage"
    }

Zeus support:
-------------

This adds support for zeus when running RSpec or Cucumber tests. First be sure that you have your copy of `RubyTest.sublime-settings` placed in User folder (refer to Settings above) and replace the following settings. ex:

    {
      "run_cucumber_command": "zeus cucumber {relative_path} --no-color",
      "run_single_cucumber_command": "zeus cucumber {relative_path}:{line_number} --no-color",

      "run_rspec_command": "zeus rspec {relative_path}",
      "run_single_rspec_command": "zeus rspec {relative_path}:{line_number}",
    }

If you use RVM/bundler, you will need to also add:

    "check_for_rvm": true

Note
----
Before reporting an issue be sure to :

  - Run Sublime Text 2 from [command line](http://www.sublimetext.com/docs/2/osx_command_line.html)

If this will not help provide to us debug informations using (CTRL + ` )

Please open an issue at https://github.com/maltize/sublime-text-2-ruby-tests if you discover a problem or would like to see a feature/change implemented.


Known issues:
-------------
[rvm and ruby 2.0 error](https://github.com/maltize/sublime-text-2-ruby-tests/issues/161)
[Run tests when Sublime Text is NOT opened from the command line on OSX] (https://github.com/maltize/sublime-text-2-ruby-tests/issues/194)
