import json
import stream
from typing import Tuple, Dict, List

STREAM_KEY = "7frnddf8dy3x"
STREAM_SECRET = "x68d3tbednets9rafzbpf5pd9nbnwzjtamjazupyj9a94jdg9e5e6zdutnyafst2"


def parse_event(event: Dict) -> Tuple[str, int]:
    params = event["Details"]["Parameters"]
    user_id = params["userId"]
    limit = int(params.get("limit", 5))
    return user_id, limit


class Items:
    def __init__(self):
        self.text_ids = []
        self.texts = []

    def add(self, text_id: str, text: str):
        if text_id not in self.text_ids:
            self.text_ids.append(text_id)
            self.texts.append(text)

    @property
    def length(self) -> int:
        return len(self.text_ids)


def get_feed_items(client,
                   user_id: str,
                   limit: int,
                   max_offset: int = 30
                   ) -> Items:
    items = Items()
    offset = 0
    forbidden_actors = [f"User:{user_id}"]
    user_feed = client.feed("basic", user_id)
    while (items.length < 5) and (offset < max_offset):
        result = user_feed.get(limit=5, offset=offset)
        for r in result["results"]:
            if r.get("actor") not in forbidden_actors:
                items.add(text_id=r["text_id"],
                          text=r["text"])
        offset += limit
    return items


def lambda_handler(event, context):
    user_id, limit = parse_event(event)

    client = stream.connect(STREAM_KEY, STREAM_SECRET)
    items = get_feed_items(client, user_id=user_id, limit=limit)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "successfully added post",
            "text_ids": items.text_ids,
            "texts": items.texts,
        }),
    }
