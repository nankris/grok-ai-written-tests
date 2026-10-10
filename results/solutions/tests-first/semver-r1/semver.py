"""SemVer 2.0.0 precedence comparison."""

_DIGITS = frozenset("0123456789")
_IDENT = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-")


def compare_semver(a: str, b: str) -> int:
    """Return -1 if *a* has lower precedence than *b*, 0 if equal, and 1 if higher.

    Build metadata does not affect precedence. Raise ValueError if either
    argument is not a valid SemVer 2.0.0 version. A leading ``v`` is rejected.
    """
    core_a, pre_a = _parse(a)
    core_b, pre_b = _parse(b)
    if core_a != core_b:
        return -1 if core_a < core_b else 1
    # A release version has higher precedence than the same core with a prerelease.
    if pre_a is None or pre_b is None:
        if pre_a is pre_b:
            return 0
        return 1 if pre_a is None else -1
    if pre_a == pre_b:
        return 0
    return -1 if pre_a < pre_b else 1


def _parse(version: str):
    if not isinstance(version, str):
        raise ValueError(f"invalid SemVer 2.0.0 version: {version!r}")

    main, separator, build = version.partition("+")
    if separator:
        _require_build(build)

    core, separator, prerelease = main.partition("-")
    numbers = _parse_core(core)
    if not separator:
        return numbers, None
    return numbers, _parse_prerelease(prerelease)


def _parse_core(core: str):
    parts = core.split(".")
    if len(parts) != 3:
        raise ValueError(f"invalid SemVer 2.0.0 version: {core!r}")
    return tuple(_parse_numeric(part) for part in parts)


def _parse_numeric(part: str) -> int:
    if not _is_digits(part) or (len(part) > 1 and part[0] == "0"):
        raise ValueError(f"invalid SemVer 2.0.0 numeric identifier: {part!r}")
    return int(part)


def _parse_prerelease(prerelease: str):
    # Numeric identifiers sort before non-numeric ones. The leading 0/1 is
    # that precedence class so ordinary tuple order matches SemVer.
    identifiers = []
    for part in prerelease.split("."):
        if part == "" or any(char not in _IDENT for char in part):
            raise ValueError(f"invalid SemVer 2.0.0 prerelease identifier: {part!r}")
        if _is_digits(part):
            if len(part) > 1 and part[0] == "0":
                raise ValueError(
                    f"invalid SemVer 2.0.0 prerelease identifier: {part!r}"
                )
            identifiers.append((0, int(part)))
        else:
            identifiers.append((1, part))
    return identifiers


def _require_build(build: str) -> None:
    for part in build.split("."):
        if part == "" or any(char not in _IDENT for char in part):
            raise ValueError(f"invalid SemVer 2.0.0 build identifier: {part!r}")


def _is_digits(part: str) -> bool:
    return part != "" and all(char in _DIGITS for char in part)
