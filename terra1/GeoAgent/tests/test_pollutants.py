from environmental.pollutants import explain_pollutant


def test_mercury():
    result = explain_pollutant("mercury")
    assert result["found"] is True


def test_microplastics():
    result = explain_pollutant("microplastics")
    assert result["found"] is True


def test_unknown_pollutant():
    result = explain_pollutant("unknown")
    assert result["found"] is False


def test_case_insensitive():
    result = explain_pollutant("MERCURY")
    assert result["found"] is True