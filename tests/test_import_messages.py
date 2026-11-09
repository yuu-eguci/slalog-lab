"""import_messages.read_latest_file のテストです。"""

from pathlib import Path

import pytest

from import_messages import read_latest_file
from tests.conftest import WriteJson


def test_read_latest_file_reads_only_the_latest_dated_file(write_json: WriteJson) -> None:
    write_json(
        "general/2023-08-01.json", [{"text": "古いメッセージ", "user": "U0000000001", "ts": "1690848000.000100"}]
    )
    write_json(
        "general/2023-08-10.json",
        [
            {
                "client_msg_id": "00000000-0000-0000-0000-000000000001",
                "type": "message",
                "text": "新しいメッセージ",
                "user": "U0000000001",
                "ts": "1691625600.000100",
                "thread_ts": "1691625600.000100",
                "replies": [{"user": "U0000000002", "ts": "1691625700.000100"}],
                "reactions": [{"name": "+1", "users": ["U0000000002"], "count": 1}],
            }
        ],
    )
    write_json("general/2023-08-09.json", [{"text": "途中のメッセージ"}])

    assert read_latest_file() == [
        {
            "client_msg_id": "00000000-0000-0000-0000-000000000001",
            "text": "新しいメッセージ",
            "user": "U0000000001",
            "ts": "1691625600.000100",
            "thread_ts": "1691625600.000100",
            "replies": [{"user": "U0000000002", "ts": "1691625700.000100"}],
            "reactions": [{"name": "+1", "users": ["U0000000002"], "count": 1}],
        }
    ]


def test_read_latest_file_ignores_files_without_date_names(write_json: WriteJson) -> None:
    write_json("general/2023-08-01.json", [{"text": "日付付きのファイル"}])
    write_json("general/2099-99-99.json", [{"text": "存在しない日付"}])
    write_json("general/notes.json", [{"text": "日付ではないファイル"}])
    write_json("general/2099-12-31.txt", [{"text": "JSON ではないファイル"}])

    messages = read_latest_file()

    assert [message["text"] for message in messages] == ["日付付きのファイル"]


def test_read_latest_file_accepts_another_channel_directory(write_json: WriteJson, logs_dir: Path) -> None:
    write_json("random/2023-08-01.json", [{"text": "random のメッセージ"}])

    messages = read_latest_file(str(logs_dir / "random"))

    assert [message["text"] for message in messages] == ["random のメッセージ"]


@pytest.mark.usefixtures("logs_dir")
def test_read_latest_file_returns_empty_list_when_directory_is_missing(capsys: pytest.CaptureFixture[str]) -> None:
    assert read_latest_file() == []
    assert "./logs/general not found." in capsys.readouterr().out


def test_read_latest_file_returns_empty_list_when_no_dated_file_exists(
    write_json: WriteJson, logs_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_json("general/notes.json", [{"text": "日付ではないファイル"}])

    assert read_latest_file(str(logs_dir / "general")) == []
    assert "No dated JSON files" in capsys.readouterr().out


def test_read_latest_file_returns_empty_list_when_path_is_a_file(
    write_json: WriteJson, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_json("general", [])

    assert read_latest_file(str(path)) == []
    assert "is not a directory" in capsys.readouterr().out
