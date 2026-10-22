from app.checks.runner import render


def test_render_spark_escaping_and_validation():
    q = render("WHERE a = {{agency}} AND d BETWEEN '{{date_from}}' AND {{date_to}}", agency="People's Association", date_from="2024-01-01", date_to="2024-12-31")
    assert q == "WHERE a = 'People\\'s Association' AND d BETWEEN '2024-01-01' AND '2024-12-31'"
    import pytest
    with pytest.raises(ValueError):
        render("{{agency}}", agency="x'; DROP TABLE t; --", date_from="2024-01-01", date_to="2024-12-31")
    with pytest.raises(ValueError):
        render("{{date_from}}", agency="HDB", date_from="2024-1-1", date_to="2024-12-31")
    with pytest.raises(ValueError):
        render("{{other}}", agency="HDB", date_from="2024-01-01", date_to="2024-12-31")


def test_tidy_number():
    from app.checks.runner import tidy_number
    assert tidy_number("113597.500000000000000000") == "113597.5" and tidy_number("90000.000") == "90000" and tidy_number("21") == "21"
    assert tidy_number("Live") == "Live" and tidy_number(None) is None
