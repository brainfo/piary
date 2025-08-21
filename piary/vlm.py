from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, List, Optional

from .types import PhotoJSON, EventStory

try:
    import ollama  # type: ignore
except Exception as e:  # pragma: no cover
    ollama = None


PHOTO_JSON_SYSTEM = (
    "You are a vision-language assistant. Given one image, produce a STRICT JSON object with keys: "
    "photo_id, caption, objects, scene_tags, people_present, num_people, vibe_words, possible_event. "
    "Return ONLY JSON. No comments, no markdown. Keep caption to 1-2 sentences."
)

PHOTO_JSON_USER_TEMPLATE = (
    "Analyze this photo. Identify salient objects and scene tags. "
    "Infer whether people are present and how many. Provide 3-6 vibe words and an optional possible event. "
    "Use the exact JSON schema specified. The photo_id is {photo_id}."
)

EVENT_STORY_SYSTEM = (
    "You are a narrative assistant. Given a set of photo summaries and event metadata, return a STRICT JSON object "
    "with keys: title (string), story (300-500 words), highlights (3-5 bullet strings). Return ONLY JSON."
)

EVENT_STORY_USER_TEMPLATE = (
    "Write a cohesive, reflective event story. Avoid repetition. Use a friendly tone.\n\n"
    "Date range: {date_range}. Location: {location_text}.\n\n"
    "Unique objects: {uniq_objects}.\n"
    "Scene tags: {uniq_scene_tags}.\n"
    "Vibe words: {uniq_vibe_words}.\n\n"
    "Here are up to {num_items} photo JSON items: {photo_items}."
)


def _read_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _ensure_json(text: str) -> Dict[str, Any]:
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json"):
            s = s[4:]
    s = s.strip()
    # Trim leading/trailing noise
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1:
        s = s[start : end + 1]
    return json.loads(s)


def infer_photo_json(
    model: str,
    image_path: str,
    photo_id: str,
    temperature: float = 0.2,
) -> PhotoJSON:
    if ollama is None:
        raise RuntimeError("ollama Python package not available. Install and run ollama.")

    image_b64 = _read_image_b64(image_path)
    user_prompt = PHOTO_JSON_USER_TEMPLATE.format(photo_id=photo_id)

    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": PHOTO_JSON_SYSTEM},
            {"role": "user", "content": user_prompt, "images": [image_b64]},
        ],
        format="json",
        options={"temperature": temperature},
    )
    text = resp.get("message", {}).get("content", "")
    data = _ensure_json(text)

    # Coerce fields
    return PhotoJSON(
        photo_id=str(data.get("photo_id", photo_id)),
        caption=str(data.get("caption", "")),
        objects=[str(x) for x in (data.get("objects") or [])],
        scene_tags=[str(x) for x in (data.get("scene_tags") or [])],
        people_present=bool(data.get("people_present", False)),
        num_people=int(data.get("num_people", 0) or 0),
        vibe_words=[str(x) for x in (data.get("vibe_words") or [])],
        possible_event=(data.get("possible_event") or None),
    )


def infer_event_story(
    model: str,
    date_range: str,
    location_text: str,
    uniq_objects: List[str],
    uniq_scene_tags: List[str],
    uniq_vibe_words: List[str],
    photo_items: List[Dict[str, Any]],
    temperature: float = 0.3,
) -> EventStory:
    if ollama is None:
        raise RuntimeError("ollama Python package not available. Install and run ollama.")

    items_str = json.dumps(photo_items)[:12000]  # trim if huge
    user_prompt = EVENT_STORY_USER_TEMPLATE.format(
        date_range=date_range,
        location_text=location_text,
        uniq_objects=", ".join(uniq_objects[:60]),
        uniq_scene_tags=", ".join(uniq_scene_tags[:60]),
        uniq_vibe_words=", ".join(uniq_vibe_words[:60]),
        num_items=min(len(photo_items), 40),
        photo_items=items_str,
    )

    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": EVENT_STORY_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        format="json",
        options={"temperature": temperature},
    )
    text = resp.get("message", {}).get("content", "")
    data = _ensure_json(text)

    highlights = data.get("highlights") or []
    if isinstance(highlights, str):
        highlights = [highlights]

    return EventStory(
        title=str(data.get("title", "Untitled Event")),
        story=str(data.get("story", "")),
        highlights=[str(x) for x in highlights][:5],
    )
