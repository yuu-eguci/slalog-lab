"""slalog.export のテストです。"""

import os
from datetime import date
from pathlib import Path

import pytest

from slalog.export import ExportDataError, load_channels, load_messages, load_users
from tests.conftest import WriteJson

EMPTY_PROFILE = {
    "real_name": None,
    "real_name_normalized": None,
    "display_name": None,
    "display_name_normalized": None,
    "image_48": None,
}


class TestLoadUsers:
    def test_extracts_selected_fields(self, write_json: WriteJson, logs_dir: Path) -> None:
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

        assert load_users(logs_dir) == [
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

    def test_fills_missing_fields_with_none(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("users.json", [{"id": "U0000000002", "profile": {}}])

        assert load_users(logs_dir) == [
            {"id": "U0000000002", "team_id": None, "name": None, "real_name": None, "profile": EMPTY_PROFILE}
        ]

    def test_treats_missing_profile_as_empty(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json(
            "users.json",
            [{"id": "B0000000001", "profile": None}, {"id": "B0000000002"}, {"id": "B0000000003", "profile": "不正"}],
        )

        assert [user["profile"] for user in load_users(logs_dir)] == [EMPTY_PROFILE, EMPTY_PROFILE, EMPTY_PROFILE]

    def test_raises_when_file_is_missing(self, logs_dir: Path) -> None:
        with pytest.raises(ExportDataError, match=r"users\.json が見つかりません"):
            load_users(logs_dir)


class TestLoadChannels:
    def test_extracts_selected_fields(self, write_json: WriteJson, logs_dir: Path) -> None:
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

        assert load_channels(logs_dir) == [
            {
                "id": "C0000000001",
                "name": "general",
                "is_archived": False,
                "members": ["U0000000001", "U0000000002"],
            },
            {"id": "C0000000002", "name": "random", "is_archived": None, "members": None},
        ]

    def test_raises_when_file_is_missing(self, logs_dir: Path) -> None:
        with pytest.raises(ExportDataError, match=r"channels\.json が見つかりません"):
            load_channels(logs_dir)


class TestInvalidJson:
    def test_raises_when_json_is_broken(self, logs_dir: Path) -> None:
        (logs_dir / "users.json").write_text("[{", encoding="utf-8")

        with pytest.raises(ExportDataError, match=r"users\.json を JSON として読み込めません"):
            load_users(logs_dir)

    def test_raises_when_top_level_is_not_a_list(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("channels.json", {"id": "C0000000001"})

        with pytest.raises(ExportDataError, match=r"channels\.json の形式が想定と異なります"):
            load_channels(logs_dir)

    def test_raises_when_item_is_not_an_object(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("general/2023-08-01.json", ["文字列だけの要素"])

        with pytest.raises(ExportDataError, match=r"2023-08-01\.json の形式が想定と異なります"):
            load_messages(logs_dir, "general")


class TestLoadMessages:
    @pytest.fixture
    def general(self, write_json: WriteJson) -> None:
        write_json("general/2023-08-01.json", [{"text": "1 日目", "user": "U0000000001", "ts": "1690848000.000100"}])
        write_json(
            "general/2023-08-10.json",
            [
                {
                    "client_msg_id": "00000000-0000-0000-0000-000000000001",
                    "type": "message",
                    "text": "10 日目",
                    "user": "U0000000001",
                    "ts": "1691625600.000100",
                    "thread_ts": "1691625600.000100",
                    "replies": [{"user": "U0000000002", "ts": "1691625700.000100"}],
                    "reactions": [{"name": "+1", "users": ["U0000000002"], "count": 1}],
                }
            ],
        )
        write_json("general/2023-08-09.json", [{"text": "9 日目"}])
        write_json("general/2099-99-99.json", [{"text": "存在しない日付"}])
        write_json("general/notes.json", [{"text": "日付ではないファイル"}])
        write_json("general/2099-12-31.txt", [{"text": "JSON ではないファイル"}])

    @pytest.mark.usefixtures("general")
    def test_reads_only_the_latest_dated_file_by_default(self, logs_dir: Path) -> None:
        assert load_messages(logs_dir, "general") == [
            {
                "client_msg_id": "00000000-0000-0000-0000-000000000001",
                "text": "10 日目",
                "user": "U0000000001",
                "ts": "1691625600.000100",
                "thread_ts": "1691625600.000100",
                "replies": [{"user": "U0000000002", "ts": "1691625700.000100"}],
                "reactions": [{"name": "+1", "users": ["U0000000002"], "count": 1}],
            }
        ]

    @pytest.mark.usefixtures("general")
    def test_reads_the_specified_date(self, logs_dir: Path) -> None:
        messages = load_messages(logs_dir, "general", day=date(2023, 8, 9))

        assert [message["text"] for message in messages] == ["9 日目"]
        assert messages[0]["user"] is None

    @pytest.mark.usefixtures("general")
    def test_reads_all_dated_files_in_date_order(self, logs_dir: Path) -> None:
        messages = load_messages(logs_dir, "general", all_dates=True)

        assert [message["text"] for message in messages] == ["1 日目", "9 日目", "10 日目"]

    @pytest.mark.usefixtures("general")
    def test_raises_when_the_specified_date_is_missing(self, logs_dir: Path) -> None:
        with pytest.raises(ExportDataError, match=r"2023-08-02\.json が見つかりません"):
            load_messages(logs_dir, "general", day=date(2023, 8, 2))

    def test_rejects_date_and_all_dates_together(self, logs_dir: Path) -> None:
        with pytest.raises(ValueError, match="同時に指定できません"):
            load_messages(logs_dir, "general", day=date(2023, 8, 1), all_dates=True)

    def test_raises_when_channel_directory_is_missing(self, logs_dir: Path) -> None:
        with pytest.raises(ExportDataError, match=r"チャンネル random のディレクトリが見つかりません"):
            load_messages(logs_dir, "random")

    def test_raises_when_channel_path_is_a_file(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("general", [])

        with pytest.raises(ExportDataError, match=r"チャンネル general のディレクトリが見つかりません"):
            load_messages(logs_dir, "general")

    def test_raises_when_no_dated_file_exists(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("general/notes.json", [])

        with pytest.raises(ExportDataError, match="日付形式の JSON ファイルがありません"):
            load_messages(logs_dir, "general")

    @pytest.mark.parametrize("channel", ["", ".", "..", "../secret", "a/b", "a\\b", "/etc"])
    def test_rejects_channel_names_that_escape_logs_dir(self, logs_dir: Path, channel: str) -> None:
        with pytest.raises(ExportDataError, match="チャンネル名が不正です"):
            load_messages(logs_dir, channel)


class TestFileSystemErrors:
    def test_raises_when_logs_dir_is_a_file(self, tmp_path: Path) -> None:
        archive = tmp_path / "export.zip"
        archive.write_bytes(b"PK")

        with pytest.raises(ExportDataError, match=r"users\.json を読み込めません"):
            load_users(archive)

    def test_raises_when_json_path_is_a_directory(self, logs_dir: Path) -> None:
        (logs_dir / "channels.json").mkdir()

        with pytest.raises(ExportDataError, match=r"channels\.json を読み込めません"):
            load_channels(logs_dir)

    @pytest.mark.skipif(
        os.name != "posix" or os.geteuid() == 0, reason="POSIX の一般ユーザーでのみ権限を検証できます。"
    )
    def test_raises_when_file_is_not_readable(self, write_json: WriteJson, logs_dir: Path) -> None:
        path = write_json("users.json", [])
        path.chmod(0)
        try:
            with pytest.raises(ExportDataError, match=r"users\.json を読み込めません"):
                load_users(logs_dir)
        finally:
            path.chmod(0o644)

    @pytest.mark.skipif(
        os.name != "posix" or os.geteuid() == 0, reason="POSIX の一般ユーザーでのみ権限を検証できます。"
    )
    def test_raises_when_channel_directory_is_not_readable(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("general/2023-08-01.json", [])
        channel_dir = logs_dir / "general"
        channel_dir.chmod(0)
        try:
            with pytest.raises(ExportDataError, match="チャンネル general のディレクトリを読み込めません"):
                load_messages(logs_dir, "general")
        finally:
            channel_dir.chmod(0o755)


class TestDatedFileNames:
    def test_ignores_names_without_zero_padding(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("general/2023-08-01.json", [{"text": "ゼロ埋めあり"}])
        write_json("general/2023-8-9.json", [{"text": "ゼロ埋めなし"}])

        assert [message["text"] for message in load_messages(logs_dir, "general", all_dates=True)] == ["ゼロ埋めあり"]

    def test_ignores_directories_with_date_names(self, write_json: WriteJson, logs_dir: Path) -> None:
        write_json("general/2023-08-01.json", [{"text": "ファイル"}])
        (logs_dir / "general" / "2023-08-05.json").mkdir()

        assert [message["text"] for message in load_messages(logs_dir, "general")] == ["ファイル"]


@pytest.mark.parametrize("channel", ["C:foo", "general:1"])
def test_rejects_channel_names_with_drive_or_colon(logs_dir: Path, channel: str) -> None:
    with pytest.raises(ExportDataError, match="チャンネル名が不正です"):
        load_messages(logs_dir, channel)
