from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict


@dataclass
class PhotoIndex:
    photo_id: str
    filepath: str
    datetime: Optional[datetime]
    lat: Optional[float]
    lon: Optional[float]


@dataclass
class PhotoJSON:
    photo_id: str
    caption: str
    objects: List[str]
    scene_tags: List[str]
    people_present: bool
    num_people: int
    vibe_words: List[str]
    possible_event: Optional[str] = None


@dataclass
class Event:
    event_id: str
    photo_ids: List[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    center_lat: Optional[float]
    center_lon: Optional[float]
    photos: List[PhotoIndex] = field(default_factory=list)


@dataclass
class EventAggregate:
    event: Event
    photos_json: List[PhotoJSON]
    location_text: Optional[str]
    uniq_objects: List[str]
    uniq_scene_tags: List[str]
    uniq_vibe_words: List[str]
    has_people: bool


@dataclass
class EventStory:
    title: str
    story: str
    highlights: List[str]


@dataclass
class MoodBoard:
    top_people: List[str]
    emotion_counts_by_person: Dict[str, Dict[str, int]]
    palette_hex: List[str]
    vibe_words_top: List[str]
