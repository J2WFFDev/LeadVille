def test_parser_imports():
    from impact_bridge.ble.parsers import (
        parse_bt50_frame,
        parse_flag61_frame,
        parse_wtvb32_frame,
        scan_and_parse,
    )

    assert callable(scan_and_parse)
    assert callable(parse_bt50_frame)
    # Legacy name should still resolve to the new implementation
    assert parse_flag61_frame is parse_bt50_frame