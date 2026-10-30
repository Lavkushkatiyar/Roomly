from app.db.base import Base
from app.db.models import HotelRoom


def test_hotel_room_table_is_registered() -> None:
    assert "hotel_rooms" in Base.metadata.tables


def test_hotel_room_columns() -> None:
    table = HotelRoom.__table__

    assert table.c.room_number.unique is True
    assert table.c.room_number.nullable is False
    assert table.c.is_active.default.arg is True
