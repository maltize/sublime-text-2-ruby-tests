require 'minitest/autorun'
require_relative 'calculator'

class StandaloneTest < Minitest::Test
  def test_add
    assert_equal 5, Calculator.add(2, 3)
  end
end
