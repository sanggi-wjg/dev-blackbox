from dev_blackbox.util.mask_util import mask


def test_visible_length():
    # given
    value = "ghp_abc123def456"

    # when
    result = mask(value, visible_length=4)

    # then
    assert result == "ghp_************"


def test_visible_length_2():
    # given
    value = "ab"

    # when
    result = mask(value, visible_length=4)

    # then
    assert result == "**"
