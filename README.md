Slalog Lab
===

📝 Slack + Export logs + Python | Slack からエクスポートしたワークスペースのデータを、Python で読み解く実験的スクリプトを保管するリポジトリです。

| 項目 | 状態 |
| --- | --- |
| Docker | 未対応です(ローカルの uv 環境で実行します) |
| 言語 | Python 3.12 以上(CI では 3.12 / 3.13 / 3.14 / 3.15 を検証しています) |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/)(`pyproject.toml` + `uv.lock`) |
| Linter / Formatter | Ruff(lint・format)、mypy(strict) |
| テスト | pytest + pytest-cov(GitHub Actions で自動実行しています) |
| 主要ライブラリ | 実行時の外部依存はありません(標準ライブラリのみ) |

## クイックスタート

1. [uv](https://docs.astral.sh/uv/getting-started/installation/) をインストールします。
2. 依存関係をインストールします。

    ```bash
    uv sync
    ```

3. Slack からエクスポートした ZIP を展開し、リポジトリ直下の `logs/` に配置します(`logs/` は Git の管理対象外です)。

    ```text
    logs/
    ├── users.json
    ├── channels.json
    └── general/
        ├── 2023-08-01.json
        └── 2023-08-02.json
    ```

4. スクリプトを実行します。

    ```bash
    uv run python import_users.py
    uv run python import_channels.py
    uv run python import_messages.py
    ```

## Slack のエクスポートデータについて

エクスポートの方法とデータの読み方は、Slack 公式のヘルプをご覧ください。

- https://slack.com/intl/ja-jp/help/articles/201658943-ワークスペースのデータをエクスポートする
- https://slack.com/intl/ja-jp/help/articles/220556107-Slack-からエクスポートしたデータの読み方

## スクリプト

| スクリプト | 読み込むファイル | 出力内容 |
| --- | --- | --- |
| `import_users.py` | `logs/users.json` | ユーザーの ID・チーム ID・名前・プロフィールの一部 |
| `import_channels.py` | `logs/channels.json` | チャンネルの ID・名前・アーカイブ状態・メンバー |
| `import_messages.py` | `logs/general/YYYY-MM-DD.json` のうち最新日付のもの | メッセージ本文・投稿者・タイムスタンプ・スレッド・リアクション |

ファイルが見つからない場合は、その旨を表示して空の結果を返します。

## Lint・型検査・テスト

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest
```

テストは `tests/` 配下にあり、合成データだけを使います。実際のエクスポートデータは使いません。
