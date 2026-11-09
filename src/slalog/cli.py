"""slalog コマンドの入口です。"""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path

from slalog.export import DATE_FORMAT, ExportDataError, load_channels, load_messages, load_users

LOGS_DIR_ENV = "SLALOG_LOGS_DIR"


def main(argv: Sequence[str] | None = None) -> int:
    """引数を解釈してエクスポートデータを読み込み、JSON として標準出力に書き出します。"""
    args = _build_parser().parse_args(argv)
    logs_dir = Path(args.logs_dir or os.environ.get(LOGS_DIR_ENV) or "logs")
    try:
        match args.command:
            case "users":
                result: object = load_users(logs_dir)
            case "channels":
                result = load_channels(logs_dir)
            case _:
                result = load_messages(logs_dir, args.channel, day=args.date, all_dates=args.all)
    except ExportDataError as e:
        print(f"slalog: エラー: {e}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
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
