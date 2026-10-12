from demo_creator.rng import rng


def test_rng_is_deterministic_and_tag_scoped():
    a = rng(1, "orders").random(3)
    b = rng(1, "orders").random(3)
    c = rng(1, "lines").random(3)
    assert list(a) == list(b)
    assert list(a) != list(c)
