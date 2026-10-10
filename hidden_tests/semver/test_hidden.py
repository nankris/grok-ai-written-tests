import pytest

from semver import compare_semver


@pytest.mark.parametrize(
    "left, right, expected",
    [
        ("1.0.0", "1.0.1", -1),
        ("1.2.0", "1.10.0", -1),
        ("1.0.0-alpha", "1.0.0", -1),
        ("1.0.0-alpha", "1.0.0-alpha.1", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1),
        ("1.0.0-rc.1", "1.0.0", -1),
        ("1.0.0-1", "1.0.0-a", -1),
        ("1.0.0-alpha.1", "1.0.0-alpha-1", -1),
        ("1.0.0+build.1", "1.0.0+build.2", 0),
        ("1.0.0-alpha+001", "1.0.0-alpha+002", 0),
        ("1.0.0+01", "1.0.0", 0),
        ("1.0.0-A", "1.0.0-a", -1),
        ("0.0.1", "0.0.1-alpha", 1),
    ],
)
def test_precedence(left, right, expected):
    assert compare_semver(left, right) == expected


@pytest.mark.parametrize(
    "text",
    ["1.0", "01.0.0", "1.0.0-01", "1.0.0-", "v1.0.0", "1.0.0-a."],
)
def test_invalid(text):
    with pytest.raises(ValueError):
        compare_semver(text, "1.0.0")
