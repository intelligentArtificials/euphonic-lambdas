import json
import stream
from dataclasses import dataclass
from typing import List, Dict
import uuid
import datetime

STREAM_KEY = "7frnddf8dy3x"
STREAM_SECRET = "x68d3tbednets9rafzbpf5pd9nbnwzjtamjazupyj9a94jdg9e5e6zdutnyafst2"


def make_tag_id(tag) -> str:
    return f"Tag_{tag}"


def get_now() -> str:
    return datetime.datetime.utcnow().isoformat()


def create_uuid() -> str:
    _id = uuid.uuid1()
    return str(_id.hex)


def parse_tags(tag_str: str) -> List[str]:
    tags = tag_str.split(",")
    tags = [t.strip() for t in tags]
    return tags


def get_object(user_type: str) -> str:
    object_mapping = {
        "human": "voxicle",
        "psaChannel": "psa",
    }
    try:
        return object_mapping[user_type]
    except KeyError:
        raise ValueError


@dataclass
class Post:
    user_id: str
    user_type: str
    post_id: str
    actor: str
    tags: List[str]
    object: str
    text: str
    text_id: str
    creation_time: str


    @classmethod
    def from_event(cls, event: Dict):
        params = event["Details"]["Parameters"]
        user_id = params.get("userId")
        if user_id is None:
            raise ValueError
        init_params = {
            "user_id": user_id,
            "user_type": params.get("userType"),
            "post_id": create_uuid(),
            "actor": f"User:{user_id}",
            "tags": parse_tags(params.get("tags", "")),
            "object": get_object(params.get("userType")),
            "text": params.get("text"),
            "text_id": create_uuid(),
            "creation_time": get_now(),
        }
        return cls(**init_params)

    def make_data_dict(self) -> Dict:
        return {
            "actor": self.actor,
            "verb": "post",
            "object": self.object,
            "tags": self.tags,
            "text": self.text,
            "text_id": self.text_id,
            "foreign_id": self.text_id,
            'to': [f"basic:{make_tag_id(tag)}" for tag in self.tags]
        }

    def add_text_to_database(self) -> str:
        return "OK"

    def add_tags_to_database(self) -> str:
        return "OK"

    def add_to_steams(self, client) -> Dict:
        user_feed = client.feed("basic", self.user_id)
        self.create_stream_users_for_tags(client)
        self.update_following(user_feed)
        activity_data = self.make_data_dict()
        activity_response = user_feed.add_activity(activity_data)
        return activity_response

    @staticmethod
    def create_tag_user_if_does_not_exist(client,  tag: str):
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

    def update_following(self, feed):
        if self.user_type == "human":
            for tag in self.tags:
                feed.follow("basic", make_tag_id(tag))


def lambda_handler(event, context):
    client = stream.connect(STREAM_KEY, STREAM_SECRET)
    post = Post.from_event(event)
    post.add_text_to_database()
    post.add_tags_to_database()
    post_data = post.add_to_steams(client)

    return {
        "statusCode": 200,
        "text_id": post.text_id,
        "post_id": post.post_id,
        "body": json.dumps({
            "message": "successfully added post",
            # "post_data": post_data,
        }),
    }
