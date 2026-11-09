"""slalog.cli のテストです。"""

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from slalog.cli import main
from tests.conftest import WriteJson


@pytest.fixture(autouse=True)
def _clear_logs_dir_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SLALOG_LOGS_DIR", raising=False)


def test_users_prints_json(write_json: WriteJson, logs_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_json("users.json", [{"id": "U0000000001", "name": "taro", "profile": {"display_name": "たろう"}}])

    assert main(["--logs-dir", str(logs_dir), "users"]) == 0

    captured = capsys.readouterr()
    assert json.loads(captured.out)[0]["profile"]["display_name"] == "たろう"
    assert "たろう" in captured.out
    assert captured.err == ""


def test_channels_reads_logs_dir_from_environment(
    write_json: WriteJson, logs_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_json("channels.json", [{"id": "C0000000001", "name": "general"}])
    monkeypatch.setenv("SLALOG_LOGS_DIR", str(logs_dir))

    assert main(["channels"]) == 0

    assert json.loads(capsys.readouterr().out) == [
        {"id": "C0000000001", "name": "general", "is_archived": None, "members": None}
    ]


def test_logs_dir_defaults_to_logs_in_current_directory(
    write_json: WriteJson, logs_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_json("channels.json", [])
    monkeypatch.chdir(logs_dir.parent)

    assert main(["channels"]) == 0
    assert json.loads(capsys.readouterr().out) == []


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ([], ["2 日目"]),
        (["--date", "2023-08-01"], ["1 日目"]),
        (["--all"], ["1 日目", "2 日目"]),
    ],
)
def test_messages_selects_files(
    write_json: WriteJson,
    logs_dir: Path,
    capsys: pytest.CaptureFixture[str],
    options: list[str],
    expected: list[str],
) -> None:
    write_json("random/2023-08-01.json", [{"text": "1 日目"}])
    write_json("random/2023-08-02.json", [{"text": "2 日目"}])

    assert main(["--logs-dir", str(logs_dir), "messages", "--channel", "random", *options]) == 0

    assert [message["text"] for message in json.loads(capsys.readouterr().out)] == expected


def test_messages_uses_general_channel_by_default(
    write_json: WriteJson, logs_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_json("general/2023-08-01.json", [{"text": "general のメッセージ"}])

    assert main(["--logs-dir", str(logs_dir), "messages"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["text"] == "general のメッセージ"


def test_reports_errors_on_stderr_with_exit_code_1(logs_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--logs-dir", str(logs_dir), "users"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "slalog: エラー:" in captured.err
    assert "users.json が見つかりません" in captured.err


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["messages", "--date", "2023/08/01"],
        ["messages", "--date", "2023-08-01", "--all"],
    ],
)
def test_rejects_invalid_arguments(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2


def test_runs_as_module(write_json: WriteJson, logs_dir: Path) -> None:
    write_json("channels.json", [{"id": "C0000000001", "name": "general"}])

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "slalog", "--logs-dir", str(logs_dir), "channels"],
        capture_output=True,
        check=True,
        encoding="utf-8",
    )

    assert json.loads(result.stdout)[0]["name"] == "general"


def test_writes_utf8_even_if_stdout_uses_another_encoding(
    write_json: WriteJson, logs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_json("channels.json", [{"id": "C0000000001", "name": "絵文字🎉"}])
    buffer = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(buffer, encoding="cp932"))

    assert main(["--logs-dir", str(logs_dir), "channels"]) == 0

    sys.stdout.flush()
    assert json.loads(buffer.getvalue().decode("utf-8"))[0]["name"] == "絵文字🎉"


def test_exits_quietly_when_pipe_is_closed(write_json: WriteJson, logs_dir: Path) -> None:
    write_json("general/2023-08-01.json", [{"text": f"メッセージ {i}" * 10} for i in range(3000)])

    with subprocess.Popen(  # noqa: S603
        [sys.executable, "-m", "slalog", "--logs-dir", str(logs_dir), "messages"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        assert process.stdout is not None
        assert process.stderr is not None
        process.stdout.read(1)
        process.stdout.close()
        stderr = process.stderr.read().decode("utf-8")
        process.wait(timeout=30)

    assert "Traceback" not in stderr
    assert "BrokenPipeError" not in stderr
