#!/usr/bin/env ruby
#
# Spin will speed up your autotest(ish) workflow for Rails.

# Spin preloads your Rails environment for testing, so you don't load the same code over and over and over... Spin works best with an autotest(ish) workflow.

require 'socket'
# This brings in `Dir.tmpdir`
require 'tempfile'
# This lets us hash the parameters we want to include in the filename
# without having to worry about subdirectories, special chars, etc.
require 'digest/md5'
# So we can tell users how much time they're saving by preloading their
# environment.
require 'benchmark'
# We use OptionParser to parse the command line.
require 'optparse'

module Spin

  # ## Spin runner class, which parses the command line and delegates the work
  # to the class matching the command requested.
  class Runner
    def initialize(arguments)
      @arguments = arguments
    end

    def run
      parser = CommandLine.new(@arguments).parse!
      worker = ::Spin.const_get(parser.command.capitalize.to_sym)
      worker.new(socket_file, parser.options).run
    end

    private

    def socket_file
      key = Digest::MD5.hexdigest [Dir.pwd, 'spin-gem'].join
      [Dir.tmpdir, key].join('/')
    end
  end

  # ## spin serve
  class Serve
    def initialize(file, options)
      @file, @options = file, options
    end

    def run
      # We delete the tmp file for the Unix socket if it already exists. The file
      # is scoped to the `pwd`, so if it already exists then it must be from an
      # old run of `spin serve` and can be cleaned up.
      File.delete(@file) if File.exist?(@file)
      # This socket is how we communicate with `spin push`.
      socket = UNIXServer.open(@file)

      ENV['RAILS_ENV'] = 'test' unless ENV['RAILS_ENV']

      if File.exist? @options[:init]
        sec = Benchmark.realtime {
          # We require config/application because that file (typically) loads Rails
          # and any Bundler deps, as well as loading the initialization code for
          # the app, but it doesn't actually perform the initialization. That happens
          # in config/environment.
          #
          # In my experience that's the best we can do in terms of preloading. Rails
          # and the gem dependencies rarely change and so don't need to be reloaded.
          # But you can't initialize the application because any non-trivial app will
          # involve it's models/controllers, etc. in its initialization, which you 
          # definitely don't want to preload.
          require File.expand_path @options[:init]
        }
        # This is the amount of time that you'll save on each subsequent test run.
        puts "Preloaded Rails env in #{sec}s..."
      else
        warn "Could not find #{@options[:init]}. Are you running this from the root of a Rails project?"
      end

      @options[:testing] ||= :rspec if defined?(RSpec)
      puts "Will run in #{@options[:testing].inspect} mode." unless @options[:testing].nil?

      loop do
        # Since `spin push` reconnects each time it has a new file for us we just
        # need to accept(2) connections from it.
        conn = socket.accept
        # This should be a relative path to a file.
        file = conn.gets.chomp

        # We fork(2) before loading the file so that our pristine preloaded
        # environment is untouched. The child process will load whatever code it
        # needs to, then it exits and we're back to the baseline preloaded app.
        fork do
          puts
          puts "Loading #{file}"

          # Unfortunately rspec's interface isn't as simple as just requiring the
          # test file that you want to run (suddenly test/unit seems like the less
          # crazy one!).
          if @options[:testing] == :rspec
            puts "RSpec mode"
            # We pretend the filepath came in as an argument and duplicate the 
            # behaviour of the `rspec` binary.
            ARGV.push file
            require 'rspec/autorun'
          else
            puts "Test unit mode"
            # We require the full path of the file here in the child process.
            $LOAD_PATH << './test'
            require File.expand_path file
          end
        end

        # We don't want the parent process handling multiple test runs at the same
        # time because then we'd need to deal with multiple test databases, and
        # that destroys the idea of being simple to use. So we wait(2) until the
        # child process has finished running the test.
        Process.wait
      end
    end
  end

  # ## spin push
  class Push
    def initialize(file, options)
      @file, @options = file, options
    end

    def run
      # This is the other end of the socket that `spin serve` opens. At this point
      # `spin serve` will accept(2) our connection.
      socket = UNIXSocket.open(@file)
      # The filenames that we will spin up to `spin serve` are passed in as 
      # arguments.
      files_to_load = @options[:files]

      # We reject anything in ARGV that isn't a file that exists. This takes
      # care of scripts that specify files like `spin push -r file.rb`. The `-r`
      # bit will just be ignored.
      files_to_load.select { |f| File.exist?(f) }.each do |f|
        puts "Spinning up #{f}"
        # We put the filename on the socket for the server to read and then load.
        socket.puts f
      end
    rescue Errno::ECONNREFUSED
      abort "Connection was refused. Have you started up `spin serve` yet?"
    end
  end

  # ## CommandLine class: parse command line
  class CommandLine
    # Once parsed, a command line instance offers access to the command to
    # run and its options.
    attr_reader :command, :options

    # Instantiate a new command line with the script an array of arguments.
    def initialize(arguments)
      @arguments = arguments.dup
      @options = {
        :init => 'config/application.rb'
      }
    end

    # Parse the arguments and sets @command and @options accordingly.
    def parse!
      parser.parse!
      @command = @arguments.shift
      raise OptionParser::MissingArgument.new("command") if @command.nil?
      raise OptionParser::InvalidArgument.new(@command) unless %w(serve push).include?(@command)
      raise OptionParser::MissingArgument.new("file(s") if @command == 'push' && @arguments.empty?
      options[:files] = @arguments
      self

    rescue OptionParser::ParseError => ex
      $stderr.puts ex
      $stderr.puts parser
      exit
    end

    private

    def parser
      @parser ||= OptionParser.new do |args|
        usage =<<-USAGE
          |Usage: spin serve [options]
          |      spin push <file>...
        USAGE
        args.banner = usage.gsub(/^ *\|/, '')

        args.separator ''
        args.separator 'Spin preloads your Rails environment to speed up your autotest(ish) workflow.'

        args.on('-t', '--test FRAMEWORK', [:test, :rspec],
                'Manually select the test framework (test, rspec)') do |value|
          options[:testing] = value
        end

        args.on('-i', '--init FILE', "Application init file (default: #{options[:init]})") do |file|
          options[:init] = file
        end

        args.on_tail('-h', '--help', 'Show this message') do
          $stderr.puts args
          exit
        end
      end
    end
  end
end

# We now run the script by instantiating a runner with our command line arguments
# and by running it.
Spin::Runner.new(ARGV).run
