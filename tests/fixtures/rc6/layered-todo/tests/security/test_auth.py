from security.auth import authorize


def test_authorize_requires_subject():
    assert authorize("operator") is True
