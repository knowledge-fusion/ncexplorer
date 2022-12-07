def test_is_valid_abstraction():
    from app.utils import is_valid_abstraction

    categories = ["Category:Articles_containing_image_maps"]

    for category in categories:
        assert not is_valid_abstraction(category)
