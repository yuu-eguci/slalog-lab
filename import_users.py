import json
from pprint import pprint


def read_users() -> list[dict[str, object | None]]:
    file_path = './logs/users.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"{file_path} not found.")
        return []

    result = []
    for user in data:
        id_ = user.get('id')
        team_id = user.get('team_id')
        name = user.get('name')
        real_name = user.get('real_name')
        profile = {
            "real_name": user['profile'].get('real_name'),
            "real_name_normalized": user['profile'].get('real_name_normalized'),
            "display_name": user['profile'].get('display_name'),
            "display_name_normalized": user['profile'].get('display_name_normalized'),
            "image_48": user['profile'].get('image_48'),
        }

        result.append({
            "id": id_,
            "team_id": team_id,
            "name": name,
            "real_name": real_name,
            "profile": profile,
        })

    return result


if __name__ == "__main__":
    users = read_users()
    pprint(users)
