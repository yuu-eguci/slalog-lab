Slalog Lab
===

📝 Slack + Export logs + Python 3.10 | Slack からエクスポートしたログを Python で整理するスクリプトだよ

## Interpret logs

Import logs

- https://slack.com/intl/ja-jp/help/articles/201658943-ワークスペースのデータをエクスポートする
- https://slack.com/intl/ja-jp/help/articles/220556107-Slack-からエクスポートしたデータの読み方

Interpret logs

```bash
pipevn run python import_users.py
pipevn run python import_channels.py
pipevn run python import_messages.py
```

## Linting

```bash
pipenv run mypy
pipenv run flake8
```
