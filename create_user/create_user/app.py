import json
import stream
from dataclasses import dataclass
from typing import List, Dict

STREAM_KEY = "7frnddf8dy3x"
STREAM_SECRET = "x68d3tbednets9rafzbpf5pd9nbnwzjtamjazupyj9a94jdg9e5e6zdutnyafst2"


def create_user_id(phone_number: str) -> str:
    return phone_number


def parse_tags(tag_str: str) -> List[str]:
    tags = tag_str.split(",")
    tags = [t.strip() for t in tags]
    return tags


@dataclass
class User:
    id: str
    phone_number: str
    type: str
    tags: List[str]
    name: str
    location: str

    @classmethod
    def from_event(cls, event: Dict):
        params = event["Details"]["Parameters"]
        init_params = {
            "id": create_user_id(params.get("phoneNumber")),
            "phone_number": params.get("phoneNumber"),
            "type": params.get("type"),
            "tags": parse_tags(params.get("tags", "")),
            "name": params.get("name"),
            "location": params.get("location"),
        }
        return cls(**init_params)

    def make_data_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type,
            "location": self.name,
            "tags": self.tags,
        }

    def add_to_database(self) -> str:
        return "OK"

    def add_to_steams(self, client):
        client.users.add(
            self.id,
            {"name": "Ye Da Ge", "gender": "male", "location": "Taibei"},
        )

    def get_streams_user_data(self, client) -> Dict:
        return client.users.get(self.id)


def lambda_handler(event, context):
    client = stream.connect(STREAM_KEY, STREAM_SECRET)
    user = User.from_event(event)

    user.add_to_database()
    user.add_to_steams(client)
    user_data = user.get_streams_user_data(client)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "sucessfully added user",
            "user_data": user_data,
            "user_id": user.id,
        }),
    }
