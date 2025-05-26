"""
Unit tests for short_codes converter module.
"""

import pytest

from composer_tools.converters.short_codes import (
    InvalidConditionError,
    generate_symphony_code,
    parse_condition,
)


def test_parse_condition_absolute():
    """Test parsing of absolute conditions."""
    result = parse_condition("RSI_14_SPY_LT_30")

    assert result["type"] == "absolute"
    assert result["metric"] == "RSI"
    assert result["window"] == "14"
    assert result["ticker"] == "SPY"
    assert result["operator"] == "LT"
    assert result["value"] == "30"


def test_parse_condition_relative():
    """Test parsing of relative conditions."""
    result = parse_condition("MA_50_SPY_LT_MA_20_SPY")

    assert result["type"] == "relative"
    assert result["metric"] == "MA"
    assert result["window1"] == "50"
    assert result["ticker1"] == "SPY"
    assert result["operator"] == "LT"
    assert result["window2"] == "20"
    assert result["ticker2"] == "SPY"


def test_parse_condition_nested():
    """Test parsing of nested conditions."""
    result = parse_condition("RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05")

    assert result["type"] == "nested"
    assert len(result["conditions"]) == 2

    first_condition = result["conditions"][0]
    assert first_condition["metric"] == "RSI"
    assert first_condition["window"] == "14"
    assert first_condition["ticker"] == "SPY"
    assert first_condition["operator"] == "LT"
    assert first_condition["value"] == "30"

    second_condition = result["conditions"][1]
    assert second_condition["metric"] == "CUMRET"
    assert second_condition["window"] == "10"
    assert second_condition["ticker"] == "SPY"
    assert second_condition["operator"] == "LT"
    assert second_condition["value"] == "0.05"


def test_parse_condition_invalid_format():
    """Test error handling for invalid condition formats."""
    with pytest.raises(InvalidConditionError, match="Invalid condition format"):
        parse_condition("INVALID_FORMAT")

    with pytest.raises(InvalidConditionError, match="Unknown metric"):
        parse_condition("BADMETRIC_14_SPY_LT_30")

    with pytest.raises(InvalidConditionError, match="Unknown operator"):
        parse_condition("RSI_14_SPY_BADOP_30")


def test_parse_condition_nested_invalid():
    """Test error handling for invalid nested conditions."""
    with pytest.raises(InvalidConditionError, match="Invalid nested condition format"):
        parse_condition("RSI_14_SPY_LT__BADFORMAT")

    with pytest.raises(InvalidConditionError, match="Nested condition requires a numeric value"):
        parse_condition("RSI_14_SPY_LT_NOTANUMBER__CUMRET_10_SPY_LT_0.05")


def test_parse_condition_relative_mismatched_metrics():
    """Test error handling for relative conditions with mismatched metrics."""
    with pytest.raises(InvalidConditionError, match="Metrics must match for relative comparison"):
        parse_condition("RSI_50_SPY_LT_MA_20_SPY")


def test_generate_symphony_code_absolute():
    """Test generation of Clojure code for absolute conditions."""
    result = generate_symphony_code("RSI_14_SPY_LT_30", "GLD", "BIL")

    expected = """(defsymphony
 "RSI_14_SPY_LT_30"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
      (< (rsi "SPY" {:window 14}) 30.0)
      [(asset "GLD")]
      [(asset "BIL")])])
)"""

    assert result == expected


def test_generate_symphony_code_relative():
    """Test generation of Clojure code for relative conditions."""
    result = generate_symphony_code("MA_50_SPY_LT_MA_20_SPY", "GLD", "BIL")

    expected = """(defsymphony
 "MA_50_SPY_LT_MA_20_SPY"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
      (< (moving-average-return "SPY" {:window 50}) (moving-average-return "SPY" {:window 20}))
      [(asset "GLD")]
      [(asset "BIL")])])
)"""

    assert result == expected


def test_generate_symphony_code_nested_double():
    """Test generation of Clojure code for double nested conditions."""
    result = generate_symphony_code("RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05", "GLD", "BIL")

    expected = """(defsymphony
 "RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
         (< (rsi "SPY" {:window 14}) 30.0)
         (if
         (< (cumulative-return "SPY" {:window 10}) 0.05)
         [(asset "GLD")]
         [(asset "BIL")])
         [(asset "BIL")])])
)"""

    assert result == expected


def test_generate_symphony_code_nested_triple():
    """Test generation of Clojure code for triple nested conditions."""
    result = generate_symphony_code("RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05__STD_20_XLU_GT_0.02", "GLD", "BIL")

    expected = """(defsymphony
 "RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05__STD_20_XLU_GT_0.02"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
         (< (rsi "SPY" {:window 14}) 30.0)
         (if
         (< (cumulative-return "SPY" {:window 10}) 0.05)
         (if
         (> (stdev-return "XLU" {:window 20}) 0.02)
         [(asset "GLD")]
         [(asset "BIL")])
         [(asset "BIL")])
         [(asset "BIL")])])
)"""

    assert result == expected


def test_generate_symphony_code_nested_quadruple():
    """Test generation of Clojure code for quadruple nested conditions."""
    result = generate_symphony_code(
        "RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05__STD_20_XLU_GT_0.02__MA_50_BND_LT_100", "GLD", "BIL"
    )

    expected = """(defsymphony
 "RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05__STD_20_XLU_GT_0.02__MA_50_BND_LT_100"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
         (< (rsi "SPY" {:window 14}) 30.0)
         (if
         (< (cumulative-return "SPY" {:window 10}) 0.05)
         (if
         (> (stdev-return "XLU" {:window 20}) 0.02)
         (if
         (< (moving-average-return "BND" {:window 50}) 100.0)
         [(asset "GLD")]
         [(asset "BIL")])
         [(asset "BIL")])
         [(asset "BIL")])
         [(asset "BIL")])])
)"""

    assert result == expected


def test_generate_symphony_code_nested_with_relative():
    """Test generation of Clojure code for nested conditions including relative comparisons."""
    # Test the specific case that was failing: relative condition in nested structure
    result = generate_symphony_code("RSI_5_XLP_LT_RSI_30_SPY__CUMRET_60_BND_GT_CUMRET_55_XLU", "SPY", "BIL")

    expected = """(defsymphony
 "RSI_5_XLP_LT_RSI_30_SPY__CUMRET_60_BND_GT_CUMRET_55_XLU"
 {:asset-class "EQUITIES", :rebalance-frequency :daily}
 (weight-equal
  [(if
         (< (rsi "XLP" {:window 5}) (rsi "SPY" {:window 30}))
         (if
         (> (cumulative-return "BND" {:window 60}) (cumulative-return "XLU" {:window 55}))
         [(asset "SPY")]
         [(asset "BIL")])
         [(asset "BIL")])])
)"""

    assert result == expected

    # Test mixed nested conditions (absolute first, then relative)
    result = generate_symphony_code("RSI_14_SPY_LT_30__CUMRET_75_XLU_LT_CUMRET_40_BND", "GLD", "BIL")
    assert '(< (rsi "SPY" {:window 14}) 30.0)' in result
    assert '(< (cumulative-return "XLU" {:window 75}) (cumulative-return "BND" {:window 40}))' in result


def test_generate_symphony_code_different_metrics():
    """Test generation for different metric types."""
    # Test CUMRET
    result = generate_symphony_code("CUMRET_10_SPY_LT_0.05", "GLD", "BIL")
    assert "cumulative-return" in result

    # Test STD
    result = generate_symphony_code("STD_20_XLU_GT_0.02", "GLD", "BIL")
    assert "stdev-return" in result

    # Test relative CUMRET
    result = generate_symphony_code("CUMRET_75_XLU_LT_CUMRET_40_BND", "GLD", "BIL")
    assert "cumulative-return" in result
    assert "XLU" in result
    assert "BND" in result


def test_generate_symphony_code_different_operators():
    """Test generation for different operators."""
    # Test GT
    result = generate_symphony_code("STD_20_XLU_GT_0.02", "GLD", "BIL")
    assert "(> " in result

    # Test LT
    result = generate_symphony_code("RSI_14_SPY_LT_30", "GLD", "BIL")
    assert "(< " in result


def test_generate_symphony_code_invalid_input():
    """Test error handling for invalid inputs."""
    with pytest.raises(InvalidConditionError):
        generate_symphony_code("INVALID_INPUT", "GLD", "BIL")


def test_generate_symphony_code_numeric_validation():
    """Test numeric validation in conditions."""
    with pytest.raises(InvalidConditionError, match="requires a numeric value"):
        generate_symphony_code("RSI_14_SPY_LT_NOTANUMBER", "GLD", "BIL")


@pytest.mark.parametrize(
    "input_str,expected_metric",
    [
        ("RSI_14_SPY_LT_30", "rsi"),
        ("STD_20_XLU_GT_0.02", "stdev-return"),
        ("CUMRET_10_SPY_LT_0.05", "cumulative-return"),
        ("MA_50_SPY_LT_MA_20_SPY", "moving-average-return"),
    ],
)
def test_metric_mappings(input_str, expected_metric):
    """Test that metric mappings are correct."""
    result = generate_symphony_code(input_str, "GLD", "BIL")
    assert expected_metric in result


@pytest.mark.parametrize(
    "input_str,expected_operator",
    [
        ("RSI_14_SPY_LT_30", "(<"),
        ("STD_20_XLU_GT_0.02", "(>"),
        ("RSI_14_SPY_EQ_30", "(="),
        ("RSI_14_SPY_LTE_30", "(<="),
        ("RSI_14_SPY_GTE_30", "(>="),
    ],
)
def test_operator_mappings(input_str, expected_operator):
    """Test that operator mappings are correct."""
    result = generate_symphony_code(input_str, "GLD", "BIL")
    assert expected_operator in result
