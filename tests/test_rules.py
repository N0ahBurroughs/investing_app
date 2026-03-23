from core.rules import parse_rules


def test_parse_rules_text():
    raw = """
    Name: Demo
    Universe: AAPL, MSFT
    Max_Position_Pct: 0.1
    Max_Risk_Score: 0.6
    Entry: Buy when price above SMA
    Exit: Sell when price below SMA
    """
    rules, mode = parse_rules(raw)
    assert mode == "text"
    assert rules.name == "Demo"
    assert "AAPL" in rules.universe
