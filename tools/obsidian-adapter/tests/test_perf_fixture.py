from scripts.perf_probe import synthetic_records


def test_synthetic_fixture_is_deterministic_and_sized():
    a = synthetic_records(1000)
    b = synthetic_records(1000)
    assert len(a) == 1000
    assert a == b
    assert a[0]["id"] == "SYN-000000"
