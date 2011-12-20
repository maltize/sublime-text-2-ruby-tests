#!/usr/bin/env ruby
# Spin will speed up your autotest(ish) workflow for Rails.

# Spin preloads your Rails environment for testing, so you don't load the same code over and over and over... Spin works best with an autotest(ish) workflow.
require 'rubygems'
require 'socket'
# This brings in `Dir.tmpdir`
require 'tempfile'
# This lets us hash the parameters we want to include in the filename
# without having to worry about subdirectories, special chars, etc.
require 'digest/md5'
# So we can tell users how much time they're saving by preloading their
# environment.
require 'benchmark'
require 'optparse'
require 'ruby-growl'

SEPARATOR = '|'
def usage
  <<-USAGE
Usage: spin serve
       spin push <file> <file>...
Spin preloads your Rails environment to speed up your autotest(ish) workflow.
  USAGE
end

def socket_file
  key = Digest::MD5.hexdigest [Dir.pwd, 'spin-gem'].join
  [Dir.tmpdir, key].join('/')
end

def determine_test_framework(force_rspec, force_testunit)
  if force_rspec
    :rspec
  elsif force_testunit
    :testunit
  elsif defined?(RSpec)
    :rspec
  else
    :testunit
  end
end

def disconnect(connection)
  connection.print "\0"
  connection.close
end

# ## spin serve
def serve(force_rspec, force_testunit, time, push_results)
  file = socket_file

  # We delete the tmp file for the Unix socket if it already exists. The file
  # is scoped to the `pwd`, so if it already exists then it must be from an
  # old run of `spin serve` and can be cleaned up.
  File.delete(file) if File.exist?(file)

  # This socket is how we communicate with `spin push`.
  socket = UNIXServer.open(file)

  ENV['RAILS_ENV'] = 'test' unless ENV['RAILS_ENV']

  test_framework = nil

  if File.exist? 'config/environment.rb'
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
      require File.expand_path 'config/environment'

      # Determine the test framework to use using the passed-in 'force' options
      # or else default to checking for defined constants.
      test_framework = determine_test_framework(force_rspec, force_testunit)

      # Preload RSpec to save some time on each test run
      begin
        require 'rspec/rails'
        require 'rspec/autorun'
      rescue LoadError
      end if test_framework == :rspec
    }
    # This is the amount of time that you'll save on each subsequent test run.
    puts "Preloaded Rails env in #{sec}s..."
  else
    warn "Could not find config/application.rb. Are you running this from the root of a Rails project?"
  end

  puts "Pushing test results back to push processes" if push_results

  loop do

    # If we're not going to push the results,
    # Trap SIGQUIT (Ctrl+\) and re-run the last files that were
    # pushed.
    if !push_results
      trap('QUIT') do
        fork_and_run(@last_files_ran, push_results, test_framework, nil)
        # See WAIT below
        Process.wait
        notify(@last_files_ran)
      end
    end

    # Since `spin push` reconnects each time it has new files for us we just
    # need to accept(2) connections from it.
    conn = socket.accept
    # This should be a list of relative paths to files.
    files = conn.gets.chomp
    files = files.split(SEPARATOR)

    # If spin is started with the time flag we will track total execution so
    # you can easily compare it with time rspec spec for example
    start = Time.now if time

    # If we're not sending results back to the push process, we can disconnect
    # it immediately.
    disconnect(conn) unless push_results

    fork_and_run(files, push_results, test_framework, conn)

    # WAIT: We don't want the parent process handling multiple test runs at the same
    # time because then we'd need to deal with multiple test databases, and
    # that destroys the idea of being simple to use. So we wait(2) until the
    # child process has finished running the test.
    Process.wait
    notify(files)
    # If we are tracking time we will output it here after everything has
    # finished running
    puts "Total execution time was #{Time.now - start} seconds" if start

    # Tests have now run. If we were pushing results to a push process, we can
    # now disconnect it.
    begin
      disconnect(conn) if push_results
    rescue Errno::EPIPE
      # Don't abort if the client already disconnected
    end
  end
end

def notify(files)
  growl = Growl.new "localhost", "ruby-growl", ["Tests output"]
  case $?
  when 0
    growl.notify "Tests output", 'Tests finished', "Well done!"
  else
    growl.notify "Tests output", 'Tests Failed',  "ERROR: #{files.join('\n')}"
  end
end

def fork_and_run(files, push_results, test_framework, conn)
  # We fork(2) before loading the file so that our pristine preloaded
  # environment is untouched. The child process will load whatever code it
  # needs to, then it exits and we're back to the baseline preloaded app.
  fork do
    # To push the test results to the push process instead of having them
    # displayed by the server, we reopen $stdout/$stderr to the open
    # connection.
    if push_results
      $stdout.reopen(conn)
      $stderr.reopen(conn)
    end

    puts
    puts "Loading #{files.inspect}"

    # Unfortunately rspec's interface isn't as simple as just requiring the
    # test file that you want to run (suddenly test/unit seems like the less
    # crazy one!).
    if test_framework == :rspec
      # We pretend the filepath came in as an argument and duplicate the
      # behaviour of the `rspec` binary.
      ARGV.push files
    else
      # We require the full path of the file here in the child process.
      files.each { |f| require File.expand_path f }
    end

  end
  @last_files_ran = files
end

# ## spin push
def push
  # The filenames that we will spin up to `spin serve` are passed in as
  # arguments.
  files_to_load = ARGV

  # We reject anything in ARGV that isn't a file that exists. This takes
  # care of scripts that specify files like `spin push -r file.rb`. The `-r`
  # bit will just be ignored.
  #
  # We build a string like `file1.rb|file2.rb` and pass it up to the server.
  f = files_to_load.select { |f| File.exist?(f.split(':')[0].to_s) }.uniq.join(SEPARATOR)
  abort if f.empty?
  puts "Spinning up #{f}"

  # This is the other end of the socket that `spin serve` opens. At this point
  # `spin serve` will accept(2) our connection.
  socket = UNIXSocket.open(socket_file)
  # We put the filenames on the socket for the server to read and then load.
  socket.puts f

   while line = socket.readline
    print line
  end
rescue Errno::ECONNREFUSED
  abort "Connection was refused. Have you started up `spin serve` yet?"
rescue EOFError
end

force_rspec = false
force_testunit = false
time = false
push_results = false
options = OptionParser.new do |opts|
  opts.banner = usage
  opts.separator ""
  opts.separator "Server Options:"

  opts.on("-I", "--load-path=DIR#{File::PATH_SEPARATOR}DIR", "Appends directory to $LOAD_PATH") do |dirs|
    $LOAD_PATH.concat(dirs.split(File::PATH_SEPARATOR))
  end

  opts.on('--rspec', 'Force the selected test framework to RSpec') do |v|
    force_rspec = v
  end

  opts.on('--test-unit', 'Force the selected test framework to Test::Unit') do |v|
    force_testunit = v
  end

  opts.on('-t', '--time', 'See total execution time for each test run') do |v|
    time = true
  end

  opts.on('--push-results', 'Push test results to the push process') do |v|
    push_results = v
  end

  opts.separator "General Options:"
  opts.on('-e', 'Stub to keep kicker happy')
  opts.on('-h', '--help') do
    $stderr.puts opts
    exit 1
  end
end
options.parse!

subcommand = ARGV.shift
case subcommand
when 'serve' then serve(force_rspec, force_testunit, time, push_results)
when 'push' then push
else
  $stderr.puts options
  exit 1
end