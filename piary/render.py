from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .types import EventAggregate, EventStory, PhotoIndex, PhotoJSON


def _file_uri(path: str) -> str:
    p = Path(path).resolve()
    return f"file://{p}"


def _fmt_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def render_event_storybook(
    out_dir: str,
    aggregate: EventAggregate,
    story: EventStory,
    palette_hex: List[str],
) -> str:
    os.makedirs(out_dir, exist_ok=True)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("storybook.html.j2")

    event = aggregate.event
    start = _fmt_date(event.start_time) if event.start_time else ""
    end = _fmt_date(event.end_time) if event.end_time else ""
    date_range = f"{start} — {end}" if start or end else ""

    photos_display = []
    pj_by_id = {pj.photo_id: pj for pj in aggregate.photos_json}
    for p in event.photos:
        pj = pj_by_id.get(p.photo_id)
        photos_display.append(
            {
                "photo_id": p.photo_id,
                "uri": _file_uri(p.filepath),
                "caption": pj.caption if pj else "",
            }
        )

    html = template.render(
        event_id=event.event_id,
        title=story.title,
        story=story.story,
        highlights=story.highlights,
        date_range=date_range,
        location_text=aggregate.location_text,
        uniq_objects=aggregate.uniq_objects,
        uniq_scene_tags=aggregate.uniq_scene_tags,
        uniq_vibe_words=aggregate.uniq_vibe_words,
        palette_hex=palette_hex,
        photos=photos_display,
        has_people=aggregate.has_people,
    )

    out_path = os.path.join(out_dir, f"event_{event.event_id}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    return out_path
