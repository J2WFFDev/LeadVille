from impact_bridge.paths import CONFIG_DB, RUNTIME_DB, SAMPLES_DB

def test_db_names():
    assert CONFIG_DB.name == "leadville.db"
    assert RUNTIME_DB.name == "leadville_runtime.db"
    assert SAMPLES_DB.name == "bt50_samples.db"