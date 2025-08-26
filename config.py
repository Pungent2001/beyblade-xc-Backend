import json
with open('values.json') as f:
    config = json.load(f)

db_path = config["db_path"]
jwt_secret = config["jwt_secret"]
port = config["port"]
