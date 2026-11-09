Slalog Lab
===

📝 Slack + Export logs + Python | Slack からエクスポートしたワークスペースのデータを、Python で読み解く実験的なコマンドラインツール `slalog` を保管するリポジトリです。

| 項目 | 状態 |
| --- | --- |
| Docker | 対応しています(`Dockerfile` + `compose.yaml`。Python 3.15-slim ベース、非 root・読み取り専用・ネットワーク無しで実行します) |
| 言語 | Python 3.12 以上(CI では 3.12 / 3.13 / 3.14 / 3.15 を検証しています) |
| パッケージ管理 | [uv](https://docs.astral.sh/uv/)(`pyproject.toml` + `uv.lock`) |
| Linter / Formatter | Ruff(lint・format)、mypy(strict) |
| テスト | pytest + pytest-cov(GitHub Actions で自動実行しています) |
| 主要ライブラリ | 実行時の外部依存はありません(標準ライブラリのみ) |

## クイックスタート

### Docker で実行する場合

1. Slack からエクスポートした ZIP を展開し、リポジトリ直下の `logs/` に配置します(`logs/` は Git の管理対象外で、Docker イメージにも含めません)。

    ```text
    logs/
    ├── users.json
    ├── channels.json
    └── general/
        ├── 2023-08-01.json
        └── 2023-08-02.json
    ```

2. イメージをビルドします。

    ```bash
    docker compose build
    ```

3. `slalog` コマンドを実行します。`logs/` はコンテナの `/logs` に読み取り専用でマウントされます。

    ```bash
    docker compose run --rm slalog users
    docker compose run --rm slalog channels
    docker compose run --rm slalog messages --channel general
    ```

### uv で実行する場合

1. [uv](https://docs.astral.sh/uv/getting-started/installation/) をインストールします。
2. 依存関係をインストールします。

    ```bash
    uv sync
    ```

3. 上記と同じ構成で `logs/` にエクスポートデータを配置し、`slalog` コマンドを実行します。

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
    - `--channel NAME`: 読み込むチャンネルです(既定は `general`)。パス区切り文字やドライブ指定(`:`)を含む名前は受け付けません。
    - `--date YYYY-MM-DD`: 指定した日付のファイルだけを読み込みます。
    - `--all`: 日付形式のファイルをすべて日付順に読み込みます。日付形式のファイルとは、`2023-08-01.json` のように月・日をゼロ埋めした `YYYY-MM-DD.json` という名前のファイルです。
    - `--date` と `--all` を省略すると、最新日付のファイルだけを読み込みます。
- 結果は UTF-8 の JSON 配列として標準出力に出力します(日本語などはエスケープせずにそのまま出力します)。`jq` や `head` などと組み合わせられます。

    ```bash
    uv run slalog messages --channel general --all | jq '.[].text'
    ```

- 欠けている項目は `null` として出力します。`profile` を持たない(またはオブジェクトではない)ユーザーは、プロフィールの各項目を `null` にします。
- ファイルやディレクトリが見つからない・読み取れない場合、JSON が壊れている場合、日付形式のファイルが無い場合は、標準エラー出力に理由を表示して終了コード 1 で終了します。

## Docker イメージについて

- `Dockerfile` はマルチステージ構成です。ビルド用ステージで uv により `uv.lock` どおりに依存を入れ、実行用ステージには仮想環境だけをコピーします。
- ベースイメージ(`python:3.15-slim`、`ghcr.io/astral-sh/uv`)はダイジェストで固定しています。
- コンテナは UID 10001 の非 root ユーザーで動き、環境変数 `SLALOG_LOGS_DIR=/logs` を既定にしています。Linux ホストでは、`logs/` 配下のファイルとディレクトリをほかのユーザーからも読み取れる権限(例: `chmod -R a+rX logs`)にしてください。
- `compose.yaml` では、ネットワーク無し・読み取り専用のルートファイルシステム・全ケーパビリティ削除・`no-new-privileges` を指定しています。
- 実行用イメージのビルド時に Debian のセキュリティ更新を適用しています。
- `.dockerignore` で `logs/`・`.git`・`.venv`・テストなどをビルドコンテキストから除外しています。

## Lint・型検査・テスト

```bash
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest
```

テストは `tests/` 配下にあり、合成データだけを使います。実際のエクスポートデータは使いません。

## CI とセキュリティ

| 仕組み | 内容 |
| --- | --- |
| CI(`.github/workflows/ci.yml`) | PR・`main` への push・毎週月曜に実行します。Ruff・mypy、Python 3.12〜3.15 の pytest、zizmor によるワークフロー検査、hadolint・イメージのビルド・合成データでのスモークテスト・grype によるイメージスキャン(修正版のある High 以上で失敗)を行います。 |
| CodeQL(`.github/workflows/codeql.yml`) | PR・`main` への push・毎週月曜に、Python と GitHub Actions のコードを解析します。 |
| Dependabot(`.github/dependabot.yml`) | uv・GitHub Actions・Docker ベースイメージの更新 PR を毎週作成します。公開から 7 日経過した版だけを対象にします。 |

ワークフローで使うアクションはコミット SHA で、Docker イメージはダイジェストで固定しています。ワークフローの権限は必要最小限にしています。
