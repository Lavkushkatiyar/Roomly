import pytest

from app.services.confirmation import (
    ConfirmationStatus,
    classify_confirmation,
)


@pytest.mark.parametrize(
    ("transcript", "expected"),
    [
        ("yes", ConfirmationStatus.CONFIRMED),
        ("YES", ConfirmationStatus.CONFIRMED),
        ("yes, that's correct", ConfirmationStatus.CONFIRMED),
        ("please do", ConfirmationStatus.CONFIRMED),
        ("no", ConfirmationStatus.DECLINED),
        ("no, cancel it", ConfirmationStatus.DECLINED),
        ("maybe", ConfirmationStatus.UNCLEAR),
        ("I think so", ConfirmationStatus.UNCLEAR),
        ("yes, please send it", ConfirmationStatus.UNCLEAR),
        ("not yes", ConfirmationStatus.UNCLEAR),
        ("", ConfirmationStatus.UNCLEAR),
    ],
)
def test_classify_confirmation(transcript, expected):
    assert classify_confirmation(transcript) == expected
