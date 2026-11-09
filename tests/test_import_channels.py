"""import_channels.read_channels のテストです。"""

import pytest

from import_channels import read_channels
from tests.conftest import WriteJson


def test_read_channels_extracts_selected_fields(write_json: WriteJson) -> None:
    write_json(
        "channels.json",
        [
            {
                "id": "C0000000001",
                "name": "general",
                "created": 1690000000,
                "is_archived": False,
                "members": ["U0000000001", "U0000000002"],
            },
            {"id": "C0000000002", "name": "random"},
        ],
    )

    assert read_channels() == [
        {
            "id": "C0000000001",
            "name": "general",
            "is_archived": False,
            "members": ["U0000000001", "U0000000002"],
        },
        {"id": "C0000000002", "name": "random", "is_archived": None, "members": None},
    ]


@pytest.mark.usefixtures("logs_dir")
def test_read_channels_returns_empty_list_when_file_is_missing(capsys: pytest.CaptureFixture[str]) -> None:
    assert read_channels() == []
    assert "./logs/channels.json not found." in capsys.readouterr().out
