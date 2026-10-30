require 'minitest/autorun'
require_relative '../calculator'

class CalculatorTest < Minitest::Test
  def test_add
    assert_equal 5, Calculator.add(2, 3)
  end

  # A small Rails-style test DSL, without an ActiveSupport dependency.
  def self.test(name, &block)
    define_method("test_#{name.gsub(/\s+/, '_')}", &block)
  end

  test 'sum > 0' do
    assert_operator Calculator.add(2, 3), :>, 0
  end
end
