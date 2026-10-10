"""SemVer 2.0.0 precedence comparison."""

_DIGITS = "0123456789"
_IDENT_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"


def compare_semver(a: str, b: str) -> int:
    """Return -1 if *a* has lower precedence than *b*, 0 if equal, and 1 if higher.

    Precedence follows Semantic Versioning 2.0.0. Build metadata is ignored.
    Raise ValueError if either argument is not a valid SemVer 2.0.0 version.
    A leading ``v`` is not accepted.
    """
    major_a, minor_a, patch_a, pre_a = _parse(a)
    major_b, minor_b, patch_b, pre_b = _parse(b)
    if (major_a, minor_a, patch_a) != (major_b, minor_b, patch_b):
        return _cmp_ints(
            (major_a, minor_a, patch_a),
            (major_b, minor_b, patch_b),
        )
    return _cmp_prerelease(pre_a, pre_b)


def _parse(version: str):
    if not isinstance(version, str):
        _reject(version)

    core_and_pre, plus, build = version.partition("+")
    if plus and not _dot_separated(build, _is_build_identifier):
        _reject(version)

    if "-" in core_and_pre:
        core, prerelease_text = core_and_pre.split("-", 1)
        if not _dot_separated(prerelease_text, _is_prerelease_identifier):
            _reject(version)
        prerelease = tuple(_prerelease_value(part) for part in prerelease_text.split("."))
    else:
        core = core_and_pre
        prerelease = None

    numbers = core.split(".")
    if len(numbers) != 3 or not all(_is_numeric_component(part) for part in numbers):
        _reject(version)
    major, minor, patch = (int(part) for part in numbers)
    return major, minor, patch, prerelease


def _reject(version: object) -> None:
    raise ValueError(f"invalid semver: {version!r}")


def _dot_separated(text: str, identifier_ok) -> bool:
    if not text:
        return False
    return all(identifier_ok(part) for part in text.split("."))


def _is_numeric_component(text: str) -> bool:
    """Non-negative decimal integer with no leading zero. ``0`` is allowed."""
    if not text or any(ch not in _DIGITS for ch in text):
        return False
    return text == "0" or text[0] != "0"


def _is_build_identifier(text: str) -> bool:
    """Build identifiers may contain leading zeros."""
    return bool(text) and all(ch in _IDENT_CHARS for ch in text)


def _is_prerelease_identifier(text: str) -> bool:
    if not _is_build_identifier(text):
        return False
    if all(ch in _DIGITS for ch in text):
        return _is_numeric_component(text)
    return True


def _prerelease_value(text: str):
    if all(ch in _DIGITS for ch in text):
        return int(text)
    return text


def _cmp_ints(left: tuple, right: tuple) -> int:
    return -1 if left < right else 1


def _cmp_prerelease(pre_a, pre_b) -> int:
    # A release version (no prerelease) has higher precedence than a prerelease.
    if pre_a is None and pre_b is None:
        return 0
    if pre_a is None:
        return 1
    if pre_b is None:
        return -1

    for ident_a, ident_b in zip(pre_a, pre_b):
        if ident_a == ident_b:
            continue
        a_num = isinstance(ident_a, int)
        b_num = isinstance(ident_b, int)
        # Numeric identifiers have lower precedence than non-numeric ones.
        if a_num and not b_num:
            return -1
        if b_num and not a_num:
            return 1
        return -1 if ident_a < ident_b else 1

    if len(pre_a) == len(pre_b):
        return 0
    # Equal shared prefix: the longer prerelease has higher precedence.
    return -1 if len(pre_a) < len(pre_b) else 1
