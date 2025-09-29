def test_parser_imports():
    from impact_bridge.ble.parsers import parse_5561, scan_and_parse, parse_flag61_frame, parse_wtvb32_frame
    assert callable(parse_5561) and callable(scan_and_parse)