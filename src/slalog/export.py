"""Slack のエクスポートデータ(JSON)を読み込み、必要な項目だけを取り出します。"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, TypedDict

DATE_FORMAT = "%Y-%m-%d"


class ExportDataError(Exception):
    """エクスポートデータが見つからない、または読み込めない場合に送出します。"""


class Profile(TypedDict):
    real_name: str | None
    real_name_normalized: str | None
    display_name: str | None
    display_name_normalized: str | None
    image_48: str | None


class User(TypedDict):
    id: str | None
    team_id: str | None
    name: str | None
    real_name: str | None
    profile: Profile


class Channel(TypedDict):
    id: str | None
    name: str | None
    is_archived: bool | None
    members: list[str] | None


class Message(TypedDict):
    client_msg_id: str | None
    text: str | None
    user: str | None
    ts: str | None
    thread_ts: str | None
    replies: list[dict[str, Any]] | None
    reactions: list[dict[str, Any]] | None


def load_users(logs_dir: Path) -> list[User]:
    """users.json からユーザーの一覧を読み込みます。"""
    users: list[User] = []
    for user in _read_records(logs_dir / "users.json"):
        # bot などプロフィールを持たないユーザーもいるため、空のプロフィールとして扱います。
        profile = user.get("profile") or {}
        users.append(
            {
                "id": user.get("id"),
                "team_id": user.get("team_id"),
                "name": user.get("name"),
                "real_name": user.get("real_name"),
                "profile": {
                    "real_name": profile.get("real_name"),
                    "real_name_normalized": profile.get("real_name_normalized"),
                    "display_name": profile.get("display_name"),
                    "display_name_normalized": profile.get("display_name_normalized"),
                    "image_48": profile.get("image_48"),
                },
            }
        )
    return users


def load_channels(logs_dir: Path) -> list[Channel]:
    """channels.json からチャンネルの一覧を読み込みます。"""
    return [
        {
            "id": channel.get("id"),
            "name": channel.get("name"),
            "is_archived": channel.get("is_archived"),
            "members": channel.get("members"),
        }
        for channel in _read_records(logs_dir / "channels.json")
    ]


def load_messages(logs_dir: Path, channel: str, *, day: date | None = None, all_dates: bool = False) -> list[Message]:
    """チャンネルのメッセージを読み込みます。

    day を指定するとその日付のファイルを、all_dates が真ならすべての日付のファイルを日付順に読み込みます。
    どちらも指定しない場合は、最新日付のファイルだけを読み込みます。
    """
    if day is not None and all_dates:
        msg = "day と all_dates は同時に指定できません。"
        raise ValueError(msg)

    channel_dir = _channel_dir(logs_dir, channel)
    if day is not None:
        files = [channel_dir / f"{day.strftime(DATE_FORMAT)}.json"]
    else:
        files = _dated_files(channel_dir)
        if not all_dates:
            files = files[-1:]

    return [
        {
            "client_msg_id": item.get("client_msg_id"),
            "text": item.get("text"),
            "user": item.get("user"),
            "ts": item.get("ts"),
            "thread_ts": item.get("thread_ts"),
            "replies": item.get("replies"),
            "reactions": item.get("reactions"),
        }
        for file in files
        for item in _read_records(file)
    ]


def _channel_dir(logs_dir: Path, channel: str) -> Path:
    """チャンネル名からディレクトリを求めます。logs ディレクトリの外を指す名前は拒否します。"""
    if channel in {"", ".", ".."} or "/" in channel or "\\" in channel:
        msg = f"チャンネル名が不正です: {channel!r}"
        raise ExportDataError(msg)
    channel_dir = logs_dir / channel
    if not channel_dir.is_dir():
        msg = f"チャンネル {channel} のディレクトリが見つかりません: {channel_dir}"
        raise ExportDataError(msg)
    return channel_dir


def _dated_files(channel_dir: Path) -> list[Path]:
    """YYYY-MM-DD.json 形式のファイルを日付の昇順で返します。"""
    dated: list[tuple[date, Path]] = []
    for file in channel_dir.iterdir():
        if file.suffix != ".json":
            continue
        try:
            day = datetime.strptime(file.stem, DATE_FORMAT).date()
        except ValueError:
            continue
        dated.append((day, file))
    if not dated:
        msg = f"{channel_dir} に日付形式の JSON ファイルがありません。"
        raise ExportDataError(msg)
    return [file for _, file in sorted(dated)]


def _read_records(file: Path) -> list[dict[str, Any]]:
    """オブジェクトの配列を格納した JSON ファイルを読み込みます。"""
    try:
        with file.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        msg = f"{file.name} が見つかりません: {file}"
        raise ExportDataError(msg) from None
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        msg = f"{file.name} を JSON として読み込めません: {e}"
        raise ExportDataError(msg) from e
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        msg = f"{file.name} の形式が想定と異なります。オブジェクトの配列である必要があります。"
        raise ExportDataError(msg)
    return data
