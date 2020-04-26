# todo: make dry; deal with replicated code across lambdas
import json
import stream
from dataclasses import dataclass
from typing import List, Dict
import datetime

STREAM_KEY = "7frnddf8dy3x"
STREAM_SECRET = "x68d3tbednets9rafzbpf5pd9nbnwzjtamjazupyj9a94jdg9e5e6zdutnyafst2"


def make_tag_id(tag) -> str:
    return f"Tag_{tag}"


def get_now() -> str:
    return datetime.datetime.utcnow().isoformat()


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
            "location": self.location,
            "tags": self.tags,
        }

    def add_to_database(self) -> str:
        return "OK"

    @staticmethod
    def create_tag_user_if_does_not_exist(client, tag: str):
        try:
            client.users.add(
                make_tag_id(tag),
                {"type": "tag", "name": tag, "creation_time": get_now()}
            )
        except stream.exceptions.StreamApiException:
            # stream user for the given tag already exists
            pass

    def create_stream_users_for_tags(self, client):
        for tag in self.tags:
            self.create_tag_user_if_does_not_exist(client, tag)

    def update_following(self, client):
        feed = client.feed("basic", self.id)
        if self.type == "human":
            for tag in self.tags:
                feed.follow("basic", make_tag_id(tag))

    def add_to_steams(self, client):
        # TODO: do not overwrite (we do this just for demo)
        try:
            client.users.add(
                self.id,
                self.make_data_dict(),
            )
        except stream.exceptions.StreamApiException:
            client.users.delete(self.id)
            client.users.add(
                self.id,
                self.make_data_dict(),
            )
        self.create_stream_users_for_tags(client)
        self.update_following(client)

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
        "user_id": user.id,
        "body": json.dumps({
            "message": "successfully added user",
            "user_data": user_data,
        }),
    }
