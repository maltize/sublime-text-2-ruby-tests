Sublime Text 2 Ruby Tests
=========================

Overview
--------
Running:

  - ruby unit tests (all tests from file / single test)
  - cucumber tests (feature / scenario)
  - rspec (full spec, single spec)

Maciej Gajek & Grzegorz Smajdor (https://github.com/gs) project.

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

Bundler support:
------------
First be sure that you have your copy of `RubyTest.sublime-settings` placed in User folder (refer to Settings above) and fill it  with below code:

    {
      "erb_exec": "bundle exec erb",
      "ruby_unit_exec": "bundle exec ruby",
      "ruby_cucumber_exec": "bundle exec cucumber -f pretty",
      "ruby_rspec_exec": "bundle exec rspec",

      "ruby_unit_folder": "test",
      "ruby_cucumber_folder": "features",
      "ruby_rspec_folder": "spec"
    }

Usage
-----

 - Run single ruby test: `Command-Shift-R`
 - Run all ruby tests from current file: `Command-Shift-T`
 - Run last ruby test(s): `Command-Shift-E`
 - Show test panel: `Command-Shift-X`
 - Check RB, ERB file syntax: `Alt-Shift-V`
 - Switching between code and test:
    - Single View: `Command-`.
    - Split View:  `Command+Ctrl+`.

Keys:
 'Command' (OSX)
 'Ctrl' (Linux / Windows)

 ![ruby_tests screenshot](https://github.com/maltize/sublime-text-2-ruby-tests/raw/master/ruby_tests.png)


Colors Issue:
------------
We have known colors issue. Please check [this thread](https://github.com/maltize/sublime-text-2-ruby-tests/issues/33#issuecomment-3553701) for temporary solution.

Note
----
Before reporting an issue be sure to :

  - Run Sublime Text 2 from [command line](http://www.sublimetext.com/docs/2/osx_command_line.html)

If this will not help provide to us debug informations using (CTRL + ` )

Please open an issue at https://github.com/maltize/sublime-text-2-ruby-tests if you discover a problem or would like to see a feature/change implemented.
