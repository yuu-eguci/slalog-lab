"""slalog コマンドの入口です。"""

import argparse
import io
import json
import os
import sys
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path

from slalog.export import (
    DATE_FORMAT,
    Channel,
    ExportDataError,
    Message,
    User,
    load_channels,
    load_messages,
    load_users,
)

LOGS_DIR_ENV = "SLALOG_LOGS_DIR"
# シェルが SIGPIPE で終了したプロセスに設定する終了コード(128 + 13)に合わせます。
EXIT_BROKEN_PIPE = 141


def main(argv: Sequence[str] | None = None) -> int:
    """引数を解釈してエクスポートデータを読み込み、JSON として標準出力に書き出します。"""
    args = _build_parser().parse_args(argv)
    logs_dir = Path(args.logs_dir or os.environ.get(LOGS_DIR_ENV) or "logs")
    try:
        result = _load(args, logs_dir)
    except ExportDataError as e:
        print(f"slalog: エラー: {e}", file=sys.stderr)
        return 1
    return _write_json(result)


def _load(args: argparse.Namespace, logs_dir: Path) -> list[User] | list[Channel] | list[Message]:
    if args.command == "users":
        return load_users(logs_dir)
    if args.command == "channels":
        return load_channels(logs_dir)
    return load_messages(logs_dir, args.channel, day=args.date, all_dates=args.all)


def _write_json(result: object) -> int:
    """結果を UTF-8 の JSON として標準出力に書き出します。"""
    # Windows などで標準出力の文字コードが UTF-8 以外でも、UTF-8 の JSON を出力します。
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        # head などで出力が途中で閉じられた場合は、トレースバックを出さずに終了します。
        # 終了時の flush で再び例外にならないよう、標準出力を /dev/null に差し替えます。
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return EXIT_BROKEN_PIPE
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slalog", description="Slack のエクスポートデータを JSON で出力します。")
    parser.add_argument(
        "--logs-dir",
        help=f"エクスポートデータのディレクトリです(既定は環境変数 {LOGS_DIR_ENV}、未設定なら logs)。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("users", help="users.json のユーザー一覧を出力します。")
    subparsers.add_parser("channels", help="channels.json のチャンネル一覧を出力します。")
    messages = subparsers.add_parser("messages", help="チャンネルのメッセージを出力します。")
    messages.add_argument("--channel", default="general", help="読み込むチャンネル名です(既定は general)。")
    selection = messages.add_mutually_exclusive_group()
    selection.add_argument("--date", type=_parse_date, help="読み込む日付(YYYY-MM-DD)です。省略時は最新日付です。")
    selection.add_argument("--all", action="store_true", help="すべての日付のファイルを日付順に読み込みます。")
    return parser


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        msg = f"YYYY-MM-DD 形式の日付を指定してください: {value!r}"
        raise argparse.ArgumentTypeError(msg) from None
