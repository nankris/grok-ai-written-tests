import pytest

from jsonpath import get_path


DOC = {
    "a": {"b": 2, "A": 7, "a.b": 9, "": 4, '"': 5, "it's": 6},
    "items": [{"name": "n0"}, {"name": "n1"}],
    "arr": [[1, 2], [3]],
    "flag": False,
}


def test_root_and_lookups():
    assert get_path(DOC, "$") == DOC
    assert get_path(DOC, "$.a.b") == 2
    assert get_path(DOC, "$.items[0].name") == "n0"
    assert get_path(DOC, "$.arr[1][0]") == 3
    assert get_path(DOC, '$.a["a.b"]') == 9
    assert get_path(DOC, "$.a['it\\'s']") == 6
    assert get_path(DOC, "$.a['']") == 4
    assert get_path(DOC, '$.a["\\""]') == 5
    assert get_path(DOC, '$.a["\\u0041"]') == 7
    assert get_path(DOC, "$.flag") is False
    assert get_path(5, "$") == 5


def test_missing_and_bounds():
    with pytest.raises(KeyError):
        get_path(DOC, "$.nope")
    with pytest.raises(IndexError):
        get_path(DOC, "$.items[2]")
    with pytest.raises(IndexError):
        get_path([], "$[0]")


def test_wrong_container_types():
    with pytest.raises(TypeError):
        get_path(DOC, "$.items.name")
    with pytest.raises(TypeError):
        get_path(DOC, "$.a[0]")
    with pytest.raises(TypeError):
        get_path(DOC, "$[0]")


@pytest.mark.parametrize(
    "path",
    [
        "",
        "a",
        "$.",
        "$.a.",
        "$.a-b",
        "$[-1]",
        "$[01]",
        "$[]",
        "$.a[",
        "$.a['unterminated]",
        "$.a[\"\\u12\"]",
        "$.a[\"\\q\"]",
        "$. items",
    ],
)
def test_malformed(path):
    with pytest.raises(ValueError):
        get_path(DOC, path)


def test_trailing_junk_after_a_valid_segment():
    with pytest.raises(ValueError):
        get_path([10, 20], "$[0] ")


def test_negative_index_does_not_wrap():
    with pytest.raises(ValueError):
        get_path(DOC["items"], "$[-1]")
