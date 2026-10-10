"""Tests for SemVer 2.0.0 precedence comparison."""

import pytest

from semver import compare_semver


def assert_equal(a: str, b: str) -> None:
    left = compare_semver(a, b)
    right = compare_semver(b, a)
    assert left == 0, f"expected {a!r} == {b!r}, got {left!r}"
    assert right == 0, f"expected {b!r} == {a!r}, got {right!r}"
    assert type(left) is int
    assert type(right) is int


def assert_lower(a: str, b: str) -> None:
    left = compare_semver(a, b)
    right = compare_semver(b, a)
    assert left == -1, f"expected {a!r} < {b!r}, got {left!r}"
    assert right == 1, f"expected {b!r} > {a!r}, got {right!r}"
    assert type(left) is int
    assert type(right) is int


def assert_strict_order(versions: list[str]) -> None:
    for i, left in enumerate(versions):
        assert_equal(left, left)
        for right in versions[i + 1 :]:
            assert_lower(left, right)


def assert_precedence_groups(groups: list[list[str]]) -> None:
    """Versions in the same group compare equal. Earlier groups are lower."""
    for group in groups:
        for i, left in enumerate(group):
            for right in group[i:]:
                assert_equal(left, right)
    for i, earlier in enumerate(groups):
        for later in groups[i + 1 :]:
            for left in earlier:
                for right in later:
                    assert_lower(left, right)


# Canonical SemVer 2.0.0 examples, including build metadata that must not
# change precedence. Within a group every pair is equal; groups increase.
CANONICAL_GROUPS = [
    ["1.0.0-alpha", "1.0.0-alpha+001", "1.0.0-alpha+20130313144700"],
    ["1.0.0-alpha.1", "1.0.0-alpha.1+build"],
    ["1.0.0-alpha.beta"],
    ["1.0.0-beta", "1.0.0-beta+exp.sha.5114f85"],
    ["1.0.0-beta.2"],
    ["1.0.0-beta.11"],
    ["1.0.0-rc.1", "1.0.0-rc.1+build.1", "1.0.0-rc.1+build.2"],
    [
        "1.0.0",
        "1.0.0+20130313144700",
        "1.0.0+21AF26D3----117B344092BD",
        "1.0.0+0",
        "1.0.0+00",
        "1.0.0+001",
        "1.0.0+-",
        "1.0.0+build-1",
    ],
]

# Core version is compared before prerelease. Minor/patch are integers, so
# 1.10.0 beats 1.9.9 and 10.0.0 beats 2.0.0.
CORE_ORDER = [
    "0.0.0",
    "0.0.1",
    "0.1.0",
    "0.9.9",
    "1.0.0-alpha",
    "1.0.0",
    "1.0.1-0",
    "1.0.1",
    "1.1.0",
    "1.2.2",
    "1.2.3-alpha",
    "1.2.3",
    "1.2.4",
    "1.3.0",
    "1.9.9",
    "1.10.0",
    "1.11.0",
    "2.0.0-0",
    "2.0.0-alpha",
    "2.0.0",
    "2.1.0",
    "2.1.1",
    "10.0.0",
    "10.0.1",
]

# Prerelease identifiers on the same core. Numeric identifiers sort as
# integers and below any non-numeric identifier. Non-numeric identifiers sort
# by ASCII code point. A longer shared prefix sorts higher.
PRERELEASE_ORDER = [
    "1.0.0-0",
    "1.0.0-0.0",
    "1.0.0-0.0.0",
    "1.0.0-0.3.7",
    "1.0.0-1",
    "1.0.0-1.0",
    "1.0.0-1.0.0",
    "1.0.0-1.a",
    "1.0.0-2",
    "1.0.0-9",
    "1.0.0-10",
    "1.0.0--",
    "1.0.0---",
    "1.0.0-0A",
    "1.0.0-0a",
    "1.0.0-9a",
    "1.0.0-A",
    "1.0.0-ALPHA",
    "1.0.0-RC",
    "1.0.0-Z",
    "1.0.0-a",
    "1.0.0-a.a",
    "1.0.0-a-",
    "1.0.0-a-b",
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-alpha.beta.1",
    "1.0.0-alpha.gamma",
    "1.0.0-alpha-1",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc",
    "1.0.0-rc.1",
    "1.0.0-rc.1.0",
    "1.0.0-x.7.z.92",
    "1.0.0-x-y-z.--",
    "1.0.0-z",
    "1.0.0",
]

VALID_VERSIONS = [
    "0.0.0",
    "0.0.1",
    "1.0.0",
    "1.2.3",
    "10.20.30",
    "1.0.0-0",
    "1.0.0-0.0.0",
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0-x.7.z.92",
    "1.0.0-x-y-z.--",
    "1.0.0-alpha+001",
    "1.0.0+20130313144700",
    "1.0.0-beta+exp.sha.5114f85",
    "1.0.0+21AF26D3----117B344092BD",
    "1.0.0-0A",
    "1.0.0-0a",
    "1.0.0--",
    "1.0.0---",
    "1.0.0----",
    "1.0.0-alpha-",
    "1.0.0-alpha-beta",
    "1.0.0+-",
    "1.0.0+--.0",
    "1.0.0-0-1",
    "1.0.0-01a",
    "1.0.0-01-1",
    "999999999999999999999.1.2",
    "1.0.0-999999999999999999999",
    "1.0.0+001.002.003",
    "2.0.0-rc.1+build.01",
    "1.0.0-a.b.c.d+e.f.g.h",
    "1.0.0-a.b+c.d",
]


INVALID_VERSIONS = [
    "",
    " ",
    "  ",
    "\t",
    "\n",
    "\r",
    "\r\n",
    "1",
    "1.0",
    "1.0.0.0",
    "1.2.3.4",
    "1.2.3.4.5",
    "01.0.0",
    "1.01.0",
    "1.0.01",
    "1.08.0",
    "00.0.0",
    "0.00.0",
    "0.0.00",
    "v1.0.0",
    "V1.0.0",
    "v1.2.3-alpha+build",
    " 1.0.0",
    "1.0.0 ",
    "1.0.0\n",
    "1.0.0\r",
    "1.0.0\r\n",
    "1.0.0\t",
    "\t1.0.0",
    "\n1.0.0",
    "1. 0.0",
    "1.0 .0",
    "1..0",
    "1.0..0",
    ".1.0.0",
    "1.0.0.",
    "+1.0.0",
    "-1.0.0",
    "1.0.0-",
    "1.0.0+",
    "1.0.0-+",
    "1.0.0-+build",
    "1.0.0-+1",
    "1.0.0-a.",
    "1.0.0+.b",
    "1.0.0-a..b",
    "1.0.0+a..b",
    "1.0.0-.",
    "1.0.0+.",
    "1.0.0-a.b.",
    "1.0.0+a.b.",
    "1.0.0-.a",
    "1.0.0+a.",
    "1.0.0-a.+b",
    "1.0.0-a+",
    "1.0.0++",
    "1.0.0+build+meta",
    "1.0.0-alpha+build+meta",
    "1.0.0-alpha+",
    "1.0.0+build.",
    "1.0.0-01",
    "1.0.0-1.02",
    "1.0.0-00",
    "1.0.0-0.0.01",
    "1.0.0-0.03",
    "1.0.0-alpha.01",
    "1.0.0-alpha.1.02",
    "1.0.0-alpha.beta.",
    "1.0.0-alpha..1",
    "1.0.0-rc..1",
    "1.0.0-rc.01",
    "1.0.0+..1",
    "1.0.0+1.",
    "1.0.0-1.",
    "1.0.0+01.02.",
    "01.0.0-alpha",
    "1.02.3+1",
    "1.2.03-1",
    "1.0.0-01+1",
    "1.0.0-alpha.01+build",
    "1.0.0+ ",
    "1.0.0- ",
    "1.0.0-a b",
    "1.0.0-alpha_beta",
    "1.0.0-alpha.beta_1",
    "1.0.0+build_meta",
    "1.0.0-*",
    "1.0.0-a!",
    "1.0.0+b?",
    "1.0.0-rc.1 ",
    " 1.0.0-rc.1",
    "1.0.0\n1.0.0",
    "1.0.0-α",
    "1.0.0-é",
    "1.0.0+ü",
    "１.0.0",
    "1.0.0-١",
    "1.0.0-1١",
    "1.0.0-١a",
    "1.0.0-a١",
    "1.0.0+١",
    "1.0.0-a\u00a0b",
    ".",
    "..",
    "...",
    "hello",
    "1.0.0.alpha",
    "1.0.+0",
    "1.+0.0",
    "=1.0.0",
    "version 1.0.0",
    "1.0.0-alpha.beta_",
    "1.0.0+build.01.",
    "1.0.0--.01",
    "1.0.0-01.a",  # first identifier is numeric with a leading zero
]


NON_STRINGS = [None, 1, 1.0, b"1.0.0", [], {}, True, False, ("1.0.0",)]


class TestPrecedence:
    def test_canonical_spec_order_ignores_build(self):
        assert_precedence_groups(CANONICAL_GROUPS)

    def test_core_numeric_order_beats_prerelease(self):
        assert_strict_order(CORE_ORDER)

    def test_prerelease_identifier_rules(self):
        assert_strict_order(PRERELEASE_ORDER)

    def test_spec_core_examples(self):
        assert_strict_order(["1.0.0", "2.0.0", "2.1.0", "2.1.1"])

    def test_numeric_components_are_not_lexical(self):
        assert_lower("2.0.0", "10.0.0")
        assert_lower("9.0.0", "10.0.0")
        assert_lower("1.9.0", "1.10.0")
        assert_lower("1.0.9", "1.0.10")
        assert_lower("1.0.0-2", "1.0.0-10")
        assert_lower("1.0.0-beta.2", "1.0.0-beta.11")
        assert_lower("1.0.0-999", "1.0.0-1000")

    def test_large_integers(self):
        assert_lower(
            "999999999999999999998.0.0",
            "999999999999999999999.0.0",
        )
        assert_lower(
            "1.0.0-999999999999999999998",
            "1.0.0-999999999999999999999",
        )
        assert_lower("1.0.0", "999999999999999999999.0.0")

    def test_prerelease_lower_than_release_even_with_build(self):
        assert_lower("1.0.0-alpha+zzz", "1.0.0")
        assert_lower("1.0.0-alpha+zzz", "1.0.0+aaa")
        assert_lower("1.0.0-0+build", "1.0.0+0")
        assert_lower("1.0.0-0", "1.0.0+build-1")

    def test_build_metadata_never_changes_precedence(self):
        assert_equal("1.0.0+build", "1.0.0")
        assert_equal("1.0.0+build", "1.0.0+other")
        assert_equal("1.0.0+001", "1.0.0+1")
        assert_equal("1.0.0+001", "1.0.0")
        assert_equal("1.0.0+00", "1.0.0+0")
        assert_equal("1.0.0+00", "1.0.0")
        assert_equal("1.0.0-1+00", "1.0.0-1+01")
        assert_equal("1.0.0-alpha+001", "1.0.0-alpha")
        assert_equal("1.0.0-alpha+001", "1.0.0-alpha+20130313144700")
        assert_equal("1.0.0-beta+exp.sha.5114f85", "1.0.0-beta")
        assert_equal("1.0.0+21AF26D3----117B344092BD", "1.0.0+20130313144700")
        assert_equal("1.0.0-x-y-z.--", "1.0.0-x-y-z.--+build.001")
        assert_equal("1.2.3-rc.1+build.1", "1.2.3-rc.1+build.2")
        assert_equal("1.0.0+-", "1.0.0")
        assert_equal("1.0.0+0.0", "1.0.0+00.01")
        assert_equal("1.0.0-a.b.c.d+e.f.g.h", "1.0.0-a.b.c.d")
        assert_equal("1.0.0-alpha.0+build", "1.0.0-alpha.0")
        assert_lower("1.0.0-a.b.c", "1.0.0-a.b.c.d+e.f.g.h")
        assert_lower("1.0.0-1+aaa", "1.0.0-2+zzz")
        assert_lower("1.0.0-alpha+zzz", "1.0.0-alpha.1+aaa")

    def test_numeric_identifier_below_non_numeric_regardless_of_ascii(self):
        # '-' (45) sorts before '9' (57) as text, but a numeric identifier
        # still has lower precedence than any non-numeric identifier.
        assert_lower("1.0.0-9", "1.0.0--")
        assert_lower("1.0.0-123", "1.0.0-abc")
        assert_lower("1.0.0-123", "1.0.0-ABC")
        assert_lower("1.0.0-123", "1.0.0--")
        assert_lower("1.0.0-999", "1.0.0-a")
        assert_lower("1.0.0-999", "1.0.0-A")
        assert_lower("1.0.0-1", "1.0.0-1a")
        assert_lower("1.0.0-1", "1.0.0--1")
        assert_lower("1.0.0-0", "1.0.0-0A")
        assert_lower("1.0.0-0", "1.0.0-0-")
        assert_lower("1.0.0-0", "1.0.0-00a")
        assert_lower("1.0.0-1", "1.0.0-01-1")
        assert_lower("1.0.0-1.999.999", "1.0.0-1.a")

    def test_ascii_code_point_order(self):
        assert_lower("1.0.0-A", "1.0.0-a")
        assert_lower("1.0.0-A", "1.0.0-Z")
        assert_lower("1.0.0-Z", "1.0.0-a")
        assert_lower("1.0.0-a", "1.0.0-z")
        assert_lower("1.0.0-ALPHA", "1.0.0-alpha")
        assert_lower("1.0.0-RC", "1.0.0-rc")
        assert_lower("1.0.0-A", "1.0.0-ALPHA")
        assert_lower("1.0.0-ALPHA", "1.0.0-RC")
        assert_lower("1.0.0-0A", "1.0.0-0a")
        assert_lower("1.0.0-9a", "1.0.0-A")
        assert_lower("1.0.0-a", "1.0.0-a-")
        assert_lower("1.0.0-a-", "1.0.0-a-b")
        assert_lower("1.0.0-alpha", "1.0.0-alpha0")
        assert_lower("1.0.0-alpha", "1.0.0-alpha-1")
        assert_lower("1.0.0--", "1.0.0---")
        assert_lower("1.0.0-a.b", "1.0.0-a-b")
        assert_lower("1.0.0-alpha.beta", "1.0.0-alpha-1")
        assert_lower("1.0.0-alpha.gamma", "1.0.0-alpha-1")

    def test_longer_prerelease_is_higher_when_prefix_matches(self):
        assert_lower("1.0.0-alpha", "1.0.0-alpha.1")
        assert_lower("1.0.0-alpha.1", "1.0.0-alpha.1.0")
        assert_lower("1.0.0-1", "1.0.0-1.0")
        assert_lower("1.0.0-rc", "1.0.0-rc.1")
        assert_lower("1.0.0-rc.1", "1.0.0-rc.1.0")
        assert_lower("1.0.0-0", "1.0.0-0.0")
        # A difference at an earlier identifier beats extra length.
        assert_lower("1.0.0-alpha.1.2", "1.0.0-alpha.2")
        assert_lower("1.0.0-1.2.3", "1.0.0-1.2.4")
        assert_lower("1.0.0-1.2", "1.0.0-1.2.3")

    def test_core_difference_ignores_prerelease_and_build(self):
        assert_lower("1.9.9", "2.0.0-alpha")
        assert_lower("1.1.9", "1.2.0-alpha")
        assert_lower("1.2.2", "1.2.3-alpha")
        assert_lower("1.0.0-zzz", "1.0.1-aaa")
        assert_lower("1.0.0+zzz", "1.0.1-0+aaa")
        assert_lower("0.9.9+build", "1.0.0-alpha")

    def test_hyphen_after_plus_is_build_not_prerelease(self):
        assert_equal("1.0.0+build-1", "1.0.0")
        assert_lower("1.0.0-build-1", "1.0.0+build-1")
        assert_lower("1.0.0-build+1", "1.0.0+build-1")

    def test_spec_example_versions_are_ordered(self):
        assert_lower("1.0.0-0.3.7", "1.0.0-x.7.z.92")
        assert_lower("1.0.0-x.7.z.92", "1.0.0-x-y-z.--")
        assert_lower("1.0.0-x-y-z.--", "1.0.0")
        assert_equal("1.0.0-alpha+001", "1.0.0-alpha+20130313144700")
        assert_lower("1.0.0-beta+exp.sha.5114f85", "1.0.0+20130313144700")

    @pytest.mark.parametrize("version", VALID_VERSIONS)
    def test_valid_version_equals_itself(self, version: str):
        assert_equal(version, version)


class TestRejection:
    @pytest.mark.parametrize("version", INVALID_VERSIONS)
    def test_invalid_version_raises(self, version):
        with pytest.raises(ValueError):
            compare_semver(version, "1.0.0")
        with pytest.raises(ValueError):
            compare_semver("1.0.0", version)
        with pytest.raises(ValueError):
            compare_semver(version, version)

    @pytest.mark.parametrize("value", NON_STRINGS)
    def test_non_string_raises_value_error(self, value):
        with pytest.raises(ValueError):
            compare_semver(value, "1.0.0")
        with pytest.raises(ValueError):
            compare_semver("1.0.0", value)

    def test_both_non_strings_raise(self):
        with pytest.raises(ValueError):
            compare_semver(None, None)
        with pytest.raises(ValueError):
            compare_semver(1, 2)

    def test_invalid_does_not_compare_even_if_cores_would_differ(self):
        pairs = [
            ("2.0.0", "1.0"),
            ("1.0", "2.0.0"),
            ("10.0.0", "9"),
            ("1.0.0", "01.0.0"),
            ("01.0.0", "1.0.0"),
            ("1.0.0", "1.0.0+"),
            ("1.0.0+", "1.0.0"),
            ("1.0.0-1", "1.0.0-01"),
            ("1.0.0-01", "1.0.0-1"),
            ("1.0.0", ""),
            ("", "1.0.0"),
            ("", ""),
            ("v1.0.0", "1.0.0"),
            ("1.0.0", "v1.0.0"),
            ("1.8.0", "1.08.0"),
            ("1.08.0", "1.8.0"),
            ("1.0.0-8", "1.0.0-08"),
            ("1.0.0+1", "1.0.0+"),
            ("1.0.0-alpha", "1.0.0-alpha "),
            ("2.0.0-alpha", "not-a-version"),
        ]
        for left, right in pairs:
            with pytest.raises(ValueError):
                compare_semver(left, right)

    def test_leading_zero_allowed_only_when_identifier_is_not_numeric(self):
        assert_equal("1.0.0-0", "1.0.0-0")
        assert_equal("1.0.0-01a", "1.0.0-01a")
        assert_lower("1.0.0-0", "1.0.0-01a")
        assert_equal("1.0.0+00", "1.0.0")
        with pytest.raises(ValueError):
            compare_semver("1.0.0-00", "1.0.0-0")
        with pytest.raises(ValueError):
            compare_semver("1.0.0-0", "1.0.0-00")
        with pytest.raises(ValueError):
            compare_semver("1.0.0-01", "1.0.0-1")

    def test_empty_pieces_from_the_spec(self):
        for version in ("1.0.0-", "1.0.0+", "1.0.0-a.", "1.0.0+.b", " ", ""):
            with pytest.raises(ValueError):
                compare_semver(version, "1.2.3")
