import json
import os
from datetime import datetime
from pprint import pprint


def read_latest_file(path: str = "./logs/general") -> list[dict] | None:
    if not os.path.exists(path):
        print(f"{path} not found.")
        return None

    # 一番新しいファイルを見つける
    files = []
    for f in os.listdir(path):
        if f.endswith('.json'):
            try:
                datetime.strptime(f[:-5], "%Y-%m-%d")
                files.append(f)
            except ValueError:
                continue

    latest_file = max(files, key=lambda x: datetime.strptime(x[:-5], "%Y-%m-%d"))
    with open(os.path.join(path, latest_file), 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 欲しいデータを整形する
    result = []
    for item in data:
        result.append({
            "client_msg_id": item.get("client_msg_id"),
            "text": item.get("text"),
            "user": item.get("user"),
            "ts": item.get("ts"),
            "thread_ts": item.get("thread_ts"),
            "replies": item.get("replies"),
            "reactions": item.get("reactions"),
        })

    return result


if __name__ == "__main__":
    messages = read_latest_file()
    if messages:
        pprint(messages)
