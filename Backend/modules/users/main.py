import json

file_path = f"./es.json"

with open(file_path, "r") as f:
    data = json.load(f)

print(data["auth_page"]["error"]["title"])


print()