from __future__ import annotations

from typing import List, Optional

from .types import Event, PhotoJSON, EventAggregate


def _uniq_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def build_event_aggregate(event: Event, photos_json: List[PhotoJSON]) -> EventAggregate:
    objects = [o for pj in photos_json for o in (pj.objects or [])]
    scene_tags = [t for pj in photos_json for t in (pj.scene_tags or [])]
    vibe_words = [v for pj in photos_json for v in (pj.vibe_words or [])]

    uniq_objects = _uniq_keep_order(objects)
    uniq_scene_tags = _uniq_keep_order(scene_tags)
    uniq_vibe_words = _uniq_keep_order(vibe_words)
    has_people = any(pj.people_present for pj in photos_json)

    location_text: Optional[str] = None
    if event.center_lat is not None and event.center_lon is not None:
        location_text = f"{event.center_lat:.4f}, {event.center_lon:.4f}"

    return EventAggregate(
        event=event,
        photos_json=photos_json,
        location_text=location_text,
        uniq_objects=uniq_objects,
        uniq_scene_tags=uniq_scene_tags,
        uniq_vibe_words=uniq_vibe_words,
        has_people=has_people,
    )
