#!/usr/bin/env bash
# Docker イメージを合成データで実行し、基本的な動作とセキュリティ設定を確認するスモークテストです。
# 使い方: scripts/docker-smoke-test.sh <イメージ名>
set -euo pipefail

image="${1:?イメージ名を指定してください。}"
logs_dir="$(mktemp -d)"
trap 'rm -rf "$logs_dir"' EXIT

mkdir -p "$logs_dir/general"
cat > "$logs_dir/users.json" <<'JSON'
[{"id": "U0000000001", "name": "taro", "profile": {"display_name": "たろう"}}, {"id": "B0000000001"}]
JSON
cat > "$logs_dir/channels.json" <<'JSON'
[{"id": "C0000000001", "name": "general", "is_archived": false}]
JSON
echo '[{"text": "古いメッセージ"}]' > "$logs_dir/general/2023-08-01.json"
echo '[{"text": "新しいメッセージ"}]' > "$logs_dir/general/2023-08-02.json"
chmod -R a+rX "$logs_dir"

run() {
  docker run --rm --read-only --network none --cap-drop ALL --security-opt no-new-privileges \
    -v "$logs_dir:/logs:ro" "$@"
}

fail() {
  echo "NG: $*" >&2
  exit 1
}

run "$image" users | grep -q '"display_name": "たろう"' || fail "users の出力が想定と異なります。"
run "$image" channels | grep -q '"name": "general"' || fail "channels の出力が想定と異なります。"
run "$image" messages | grep -q '新しいメッセージ' || fail "messages が最新日付を読み込んでいません。"
run "$image" messages --all | grep -q '古いメッセージ' || fail "messages --all が全日付を読み込んでいません。"

if run "$image" messages --channel random 2>/dev/null; then
  fail "存在しないチャンネルで終了コード 0 になりました。"
fi

[[ "$(run --entrypoint id "$image" -u)" == "10001" ]] || fail "コンテナが UID 10001 で実行されていません。"

echo "OK: Docker スモークテストが成功しました。"
