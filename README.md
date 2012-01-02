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

 - OS X: ~/Library/Application Support/Sublime Text 2/Packages/
 - Windows: %APPDATA%/Sublime Text 2/Packages/
 - Linux: ~/.Sublime Text 2/Packages/

and clone the repository using the command below:

git clone https://github.com/maltize/sublime-text-2-ruby-tests.git RubyTest

Settings
--------

You can specify different binary for each type of test to use.

Make a copy of RubyTest.sublime-settings to Packages/User and make your changes.

Usage
-----

 - Run single ruby test: Command-Shift-R
 - Run all ruby tests from current file: Command-Shift-T
 - Run last ruby test(s): Command-Shift-E
 - Show test panel: Command-Shift-X
 - Check RB, ERB file syntax: Alt-Shift-V
 - Switching between code and test:
        - Single View: Command-.
        - Split View:  Command+Ctrl+.
Keys:
 'Command' (OSX)
 'Ctrl' (Linux / Windows)

 ![ruby_tests screenshot](https://github.com/maltize/sublime-text-2-ruby-tests/raw/master/ruby_tests.png)

Note
----
If you having trouble running tests try to run Sublime Text 2 from command line.

This is a work in progress so expect bugs.
Please open an issue at https://github.com/maltize/sublime-text-2-ruby-tests if you discover a problem or would like to see a feature/change implemented.