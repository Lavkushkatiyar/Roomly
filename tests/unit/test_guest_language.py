from app.db.models.enums import GuestLanguage


def test_guest_languages_cover_supported_concierge_languages() -> None:
    assert {language.value for language in GuestLanguage} == {
        "en-IN",
        "hi-IN",
        "hi-en",
        "ta-IN",
        "te-IN",
        "kn-IN",
        "ml-IN",
        "mr-IN",
        "bn-IN",
        "gu-IN",
        "pa-IN",
    }
