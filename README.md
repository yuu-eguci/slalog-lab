Slalog Lab
===

📝 Slack + Export logs + Python | Slack からエクスポートしたワークスペースのデータを、Python で読み解く実験的なコマンドラインツール `slalog` を保管するリポジトリです。

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

4. `slalog` コマンドを実行します。

    ```bash
    uv run slalog users
    uv run slalog channels
    uv run slalog messages --channel general
    ```

## Slack のエクスポートデータについて

エクスポートの方法とデータの読み方は、Slack 公式のヘルプをご覧ください。

- https://slack.com/intl/ja-jp/help/articles/201658943-ワークスペースのデータをエクスポートする
- https://slack.com/intl/ja-jp/help/articles/220556107-Slack-からエクスポートしたデータの読み方

## 使い方

```text
slalog [--logs-dir DIR] {users,channels,messages} ...
```

| コマンド | 読み込むファイル | 出力内容 |
| --- | --- | --- |
| `slalog users` | `users.json` | ユーザーの ID・チーム ID・名前・プロフィールの一部 |
| `slalog channels` | `channels.json` | チャンネルの ID・名前・アーカイブ状態・メンバー |
| `slalog messages` | `<チャンネル名>/YYYY-MM-DD.json` | メッセージ本文・投稿者・タイムスタンプ・スレッド・リアクション |

- `--logs-dir` でエクスポートデータのディレクトリを指定します。省略時は環境変数 `SLALOG_LOGS_DIR`、それも未設定なら `logs` を使います。
- `messages` のオプションは次のとおりです。
    - `--channel NAME`: 読み込むチャンネルです(既定は `general`)。パス区切り文字を含む名前は受け付けません。
    - `--date YYYY-MM-DD`: 指定した日付のファイルだけを読み込みます。
    - `--all`: 日付形式のファイルをすべて日付順に読み込みます。
    - `--date` と `--all` を省略すると、最新日付のファイルだけを読み込みます。
- 結果は UTF-8 の JSON 配列として標準出力に出力するため、`jq` などと組み合わせられます。

    ```bash
    uv run slalog messages --channel general --all | jq '.[].text'
    ```

- 欠けている項目は `null` として出力します。`profile` を持たないユーザーは、プロフィールの各項目を `null` にします。
- ファイルやディレクトリが見つからない場合、JSON が壊れている場合、日付形式のファイルが無い場合は、標準エラー出力に理由を表示して終了コード 1 で終了します。

## Lint・型検査・テスト

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest
```

テストは `tests/` 配下にあり、合成データだけを使います。実際のエクスポートデータは使いません。
