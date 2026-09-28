"""Template rendering: key commands and template commands, as documented on Template."""

import pytest

from gsconfig import Template


@pytest.mark.parametrize(
    ("body", "balance", "expected"),
    [
        ("{% a!float %}", {"a": 10}, "10.0"),
        ("{% a!int %}", {"a": 10.9}, "10"),
        ("{% a!get_2 %}", {"a": ["Zero", "One", "Two"]}, "Two"),
        ("{% a!extract %}", {"a": [{"x": 1}]}, '{"x": 1}'),
    ],
    ids=["float", "int", "get_N", "extract"],
)
def test_key_command(body, balance, expected):
    assert Template(body=body).render(balance) == expected


@pytest.mark.parametrize(
    ("body", "balance", "expected"),
    [
        ("{% if f %}yes{% endif %}|{% if g %}no{% endif %}", {"f": True, "g": False}, "yes|"),
        ("{% comment %}gone{% endcomment %}kept", {}, "kept"),
        ("{% foreach xs %}[$item]{% endforeach %}", {"xs": [1, 2, 3]}, "[1][2][3]"),
        ("{% for n %}<$i>{% endfor %}", {"n": 3}, "<0><1><2>"),
        ("{# note #}x", {}, "x"),
    ],
    ids=["if", "comment", "foreach", "for", "inline-comment"],
)
def test_template_command(body, balance, expected):
    assert Template(body=body).render(balance) == expected


def test_every_default_key_command_is_callable():
    # Walks the real registry so a new command without a handler fails here.
    for pattern, handler in Template.DEFAULT_KEY_COMMAND_HANDLERS.items():
        assert callable(handler), pattern
