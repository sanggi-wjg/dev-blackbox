from dev_blackbox.core.cache import resolve_cache_key


def test_resolve_cache_key():
    # given
    def iam_function(text: str, *args, **kwargs):
        return f"{text} / {args} / {kwargs}"

    key_template = "iam_function:text:{text}:args:{args}:kwargs:{kwargs}"

    # when
    key = resolve_cache_key(key_template, iam_function, "test", 1, 2, a=3, b=4)

    # then
    assert key == "iam_function:text:test:args:(1, 2):kwargs:{'a': 3, 'b': 4}"
