"""
Converter for short code notation to Composer's Clojure-like defsymphony expressions.

This module parses condition strings and asset pairs to generate Clojure code
for financial portfolio management strategies.
"""

from typing import Any, Dict, List

# Operator mappings for condition evaluation
OPERATORS = {
    "LT": "<",
    "GT": ">",
    "EQ": "=",
    "LTE": "<=",
    "GTE": ">=",
}

# Metric mappings to Composer function names
METRICS = {
    "RSI": "rsi",
    "STD": "stdev-return",
    "CUMRET": "cumulative-return",
    "MA": "moving-average",
}

# Constants for validation
EXPECTED_ABSOLUTE_PARTS = 5
EXPECTED_RELATIVE_PARTS = 7
CONDITION_SEPARATOR = "__"
PART_SEPARATOR = "_"
ASSET_SEPARATOR = ","
SPACE_SEPARATOR = " "


class InvalidConditionError(ValueError):
    """Raised when a condition string cannot be parsed."""

    pass


def _validate_numeric_value(value: str, context: str) -> float:
    """
    Validate that a string can be converted to a float.

    Args:
        value: String value to validate
        context: Context for error message

    Returns:
        Float value

    Raises:
        InvalidConditionError: If value is not numeric
    """
    try:
        return float(value)
    except ValueError:
        raise InvalidConditionError(f"{context} requires a numeric value, got: {value}")


def _parse_nested_conditions(conditions: List[str]) -> Dict[str, Any]:
    """
    Parse multiple nested conditions.

    Args:
        conditions: List of condition strings

    Returns:
        Dictionary with parsed nested conditions

    Raises:
        InvalidConditionError: If any condition is invalid
    """
    parsed_conditions = []

    for cond in conditions:
        parts = cond.split(PART_SEPARATOR)

        if len(parts) != EXPECTED_ABSOLUTE_PARTS:
            raise InvalidConditionError(f"Invalid nested condition format: {cond}")

        if parts[0] not in METRICS:
            raise InvalidConditionError(f"Unknown metric in nested condition: {parts[0]}")

        if parts[3] not in OPERATORS:
            raise InvalidConditionError(f"Unknown operator in nested condition: {parts[3]}")

        _validate_numeric_value(parts[4], "Nested condition")

        parsed_conditions.append(
            {
                "metric": parts[0],
                "window": parts[1],
                "ticker": parts[2],
                "operator": parts[3],
                "value": parts[4],
            }
        )

    return {"type": "nested", "conditions": parsed_conditions}


def _parse_absolute_condition(parts: List[str]) -> Dict[str, Any]:
    """
    Parse an absolute comparison condition.

    Args:
        parts: Split condition parts

    Returns:
        Dictionary with parsed absolute condition

    Raises:
        InvalidConditionError: If condition is invalid
    """
    if parts[0] not in METRICS:
        raise InvalidConditionError(f"Unknown metric: {parts[0]}")

    if parts[3] not in OPERATORS:
        raise InvalidConditionError(f"Unknown operator: {parts[3]}")

    _validate_numeric_value(parts[4], "Absolute comparison")

    return {
        "type": "absolute",
        "metric": parts[0],
        "window": parts[1],
        "ticker": parts[2],
        "operator": parts[3],
        "value": parts[4],
    }


def _parse_relative_condition(parts: List[str]) -> Dict[str, Any]:
    """
    Parse a relative comparison condition.

    Args:
        parts: Split condition parts

    Returns:
        Dictionary with parsed relative condition

    Raises:
        InvalidConditionError: If condition is invalid
    """
    metric1, window1, ticker1, op, metric2, window2, ticker2 = parts

    if metric1 not in METRICS or metric2 not in METRICS:
        raise InvalidConditionError("Unknown metric in relative comparison")

    if op not in OPERATORS:
        raise InvalidConditionError(f"Unknown operator in relative comparison: {op}")

    if metric1 != metric2:
        raise InvalidConditionError("Metrics must match for relative comparison")

    return {
        "type": "relative",
        "metric": metric1,
        "window1": window1,
        "ticker1": ticker1,
        "operator": op,
        "window2": window2,
        "ticker2": ticker2,
    }


def parse_condition(condition_str: str) -> Dict[str, Any]:
    """
    Parse a condition string into structured components.

    Args:
        condition_str: Condition string to parse

    Returns:
        Dictionary containing parsed condition data

    Raises:
        InvalidConditionError: If condition format is invalid
    """
    conditions = condition_str.split(CONDITION_SEPARATOR)

    # Handle nested conditions (multiple conditions joined with __)
    if len(conditions) > 1:
        return _parse_nested_conditions(conditions)

    # Handle single condition
    parts = condition_str.split(PART_SEPARATOR)

    # Absolute comparison (e.g., RSI_14_SPY_LT_30)
    if len(parts) == EXPECTED_ABSOLUTE_PARTS:
        return _parse_absolute_condition(parts)

    # Relative comparison (e.g., MA_50_SPY_LT_MA_20_SPY)
    elif len(parts) == EXPECTED_RELATIVE_PARTS:
        return _parse_relative_condition(parts)

    else:
        raise InvalidConditionError(f"Invalid condition format: {condition_str}")


def _build_condition_expression(
    metric: str,
    ticker: str,
    window: str,
    operator: str,
    value: str,
) -> str:
    """
    Build a Clojure condition expression.

    Args:
        metric: Metric name
        ticker: Ticker symbol
        window: Window parameter
        operator: Comparison operator
        value: Comparison value

    Returns:
        Formatted Clojure condition expression
    """
    clojure_op = OPERATORS[operator]
    clojure_metric = METRICS[metric]
    numeric_value = _validate_numeric_value(value, "Condition expression")

    return f'({clojure_op} ({clojure_metric} "{ticker}" {{:window {window}}}) {numeric_value})'


def _build_relative_condition_expression(
    metric: str,
    ticker1: str,
    window1: str,
    operator: str,
    ticker2: str,
    window2: str,
) -> str:
    """
    Build a Clojure relative condition expression.

    Args:
        metric: Metric name
        ticker1: First ticker symbol
        window1: First window parameter
        operator: Comparison operator
        ticker2: Second ticker symbol
        window2: Second window parameter

    Returns:
        Formatted Clojure relative condition expression
    """
    clojure_op = OPERATORS[operator]
    clojure_metric = METRICS[metric]

    return (
        f"({clojure_op} "
        f'({clojure_metric} "{ticker1}" {{:window {window1}}}) '
        f'({clojure_metric} "{ticker2}" {{:window {window2}}}))'
    )


def _generate_nested_if_expression(
    conditions: List[Dict[str, str]], index: int, asset1_expr: str, asset2_expr: str
) -> str:
    """
    Recursively generate nested if statements.

    Args:
        conditions: List of condition dictionaries
        index: Current condition index
        asset1_expr: Asset expression for true condition
        asset2_expr: Asset expression for false condition

    Returns:
        Nested Clojure if expression
    """
    if index >= len(conditions):
        return asset1_expr

    condition = conditions[index]
    condition_expr = _build_condition_expression(
        condition["metric"], condition["ticker"], condition["window"], condition["operator"], condition["value"]
    )

    next_level = _generate_nested_if_expression(conditions, index + 1, asset1_expr, asset2_expr)

    return f"(if\n         {condition_expr}\n         {next_level}\n         {asset2_expr})"


def _format_defsymphony(condition_str: str, body: str) -> str:
    """
    Format the complete defsymphony expression.

    Args:
        condition_str: Original condition string for naming
        body: Body content of the symphony

    Returns:
        Formatted defsymphony expression
    """
    return f"""(defsymphony
 "{condition_str}"
 {{:asset-class "EQUITIES", :rebalance-frequency :daily}}
 (weight-equal
  [{body}])
)"""


def generate_symphony_code(input_str: str) -> str:
    """
    Generate Composer defsymphony code from input string.

    Args:
        input_str: Input string in format 'CONDITION ASSET1,ASSET2'

    Returns:
        Generated Clojure code

    Raises:
        InvalidConditionError: If input format is invalid

    Example:
        >>> generate_symphony_code("RSI_14_SPY_LT_30 GLD,BIL")
    """
    try:
        condition_str, assets_str = input_str.split(SPACE_SEPARATOR)
    except ValueError:
        raise InvalidConditionError("Input must contain condition and assets separated by space")

    assets = assets_str.split(ASSET_SEPARATOR)
    if len(assets) != 2:
        raise InvalidConditionError("Exactly two assets must be provided")

    condition = parse_condition(condition_str)

    asset1_expr = f'[(asset "{assets[0]}")]'
    asset2_expr = f'[(asset "{assets[1]}")]'

    if condition["type"] == "nested":
        nested_if = _generate_nested_if_expression(condition["conditions"], 0, asset1_expr, asset2_expr)
        body = nested_if

    elif condition["type"] == "absolute":
        condition_expr = _build_condition_expression(
            condition["metric"],
            condition["ticker"],
            condition["window"],
            condition["operator"],
            condition["value"],
        )
        body = f"(if\n      {condition_expr}\n      {asset1_expr}\n      {asset2_expr})"

    else:  # relative
        condition_expr = _build_relative_condition_expression(
            condition["metric"],
            condition["ticker1"],
            condition["window1"],
            condition["operator"],
            condition["ticker2"],
            condition["window2"],
        )
        body = f"(if\n      {condition_expr}\n      {asset1_expr}\n      {asset2_expr})"

    return _format_defsymphony(condition_str, body)


def main():
    # Test cases
    test_inputs = [
        "RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05__STD_20_XLU_GT_0.02__MA_50_BND_LT_100 GLD,BIL",  # Quadruple nested
        "RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05__STD_20_XLU_GT_0.02 GLD,BIL",  # Triple nested
        "RSI_14_SPY_LT_30__CUMRET_10_SPY_LT_0.05 GLD,BIL",  # Double nested
        "CUMRET_10_SPY_LT_0.05 GLD,BIL",  # Absolute
        "RSI_14_SPY_LT_30 GLD,BIL",  # Absolute
        "STD_20_XLU_GT_0.02 GLD,BIL",  # Absolute
        "MA_50_SPY_LT_MA_20_SPY GLD,BIL",  # Relative
        "CUMRET_75_XLU_LT_CUMRET_40_BND GLD,BIL",  # Relative
    ]

    for input_str in test_inputs:
        try:
            print(f"\nInput: {input_str}")
            print("Generated symphony code:")
            print(generate_symphony_code(input_str))
        except Exception as e:
            print(f"Error processing {input_str}: {e}")


if __name__ == "__main__":
    main()
