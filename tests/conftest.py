"""テスト全体で使う共通のフィクスチャです。"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

type WriteJson = Callable[[str, Any], Path]


@pytest.fixture
def logs_dir(tmp_path: Path) -> Path:
    """合成データを置くための空の logs ディレクトリを用意します。"""
    path = tmp_path / "logs"
    path.mkdir()
    return path


@pytest.fixture
def write_json(logs_dir: Path) -> WriteJson:
    """logs ディレクトリからの相対パスへ、合成データを JSON として書き込む関数を返します。"""

    def _write(relative_path: str, data: Any) -> Path:
        path = logs_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    return _write
