"""import_users.read_users のテストです。"""

import pytest

from import_users import read_users
from tests.conftest import WriteJson


def test_read_users_extracts_selected_fields(write_json: WriteJson) -> None:
    write_json(
        "users.json",
        [
            {
                "id": "U0000000001",
                "team_id": "T0000000001",
                "name": "taro",
                "real_name": "山田 太郎",
                "deleted": False,
                "profile": {
                    "real_name": "山田 太郎",
                    "real_name_normalized": "山田 太郎",
                    "display_name": "たろう",
                    "display_name_normalized": "たろう",
                    "image_48": "https://example.com/taro_48.png",
                    "email": "taro@example.com",
                },
            }
        ],
    )

    assert read_users() == [
        {
            "id": "U0000000001",
            "team_id": "T0000000001",
            "name": "taro",
            "real_name": "山田 太郎",
            "profile": {
                "real_name": "山田 太郎",
                "real_name_normalized": "山田 太郎",
                "display_name": "たろう",
                "display_name_normalized": "たろう",
                "image_48": "https://example.com/taro_48.png",
            },
        }
    ]


def test_read_users_fills_missing_fields_with_none(write_json: WriteJson) -> None:
    write_json("users.json", [{"id": "U0000000002", "profile": {}}])

    assert read_users() == [
        {
            "id": "U0000000002",
            "team_id": None,
            "name": None,
            "real_name": None,
            "profile": {
                "real_name": None,
                "real_name_normalized": None,
                "display_name": None,
                "display_name_normalized": None,
                "image_48": None,
            },
        }
    ]


@pytest.mark.usefixtures("logs_dir")
def test_read_users_returns_empty_list_when_file_is_missing(capsys: pytest.CaptureFixture[str]) -> None:
    assert read_users() == []
    assert "./logs/users.json not found." in capsys.readouterr().out
