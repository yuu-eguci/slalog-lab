import json
from typing import Any
from pprint import pprint


def read_channels() -> list[dict[str, Any]]:
    file_path = './logs/channels.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"{file_path} not found.")
        return []
    return [
        {
            "id": channel.get("id", None),
            "name": channel.get("name", None),
            "is_archived": channel.get("is_archived", None),
            "members": channel.get("members", None)
        }
        for channel in data
    ]


if __name__ == '__main__':
    channels = read_channels()
    pprint(channels)
