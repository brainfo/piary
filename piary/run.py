from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import List

from tqdm import tqdm

from .scanner import scan_photos
from .cluster import cluster_events
from .vlm import infer_photo_json, infer_event_story
from .aggregate import build_event_aggregate
from .palette import dominant_palette
from .types import PhotoJSON


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _date_range_text(start, end) -> str:
    def fmt(d):
        return d.strftime("%Y-%m-%d") if d else ""

    s = fmt(start)
    e = fmt(end)
    if s and e and s != e:
        return f"{s} — {e}"
    return s or e or ""


def main() -> None:
    ap = argparse.ArgumentParser(description="Ananda: one-model memory storybooks (local only)")
    ap.add_argument("--photo-dir", required=True, help="Directory of photos (JPEG/PNG)")
    ap.add_argument("--out-dir", default="./out", help="Output directory")
    ap.add_argument("--model", default="llava:13b", help="Ollama model name (e.g., llava:13b, qwen2-vl:7b)")
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.25)
    ap.add_argument("--time-gap-hours", type=float, default=6.0)
    ap.add_argument("--distance-gap-km", type=float, default=80.0)
    ap.add_argument("--min-event-size", type=int, default=3)
    ap.add_argument("--max-photos-per-event", type=int, default=40)
    ap.add_argument("--recompute", action="store_true", help="Ignore cache and recompute per-photo JSON")
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    cache_dir = os.path.join(out_dir, ".cache", "photo_json")
    _ensure_dir(cache_dir)
    _ensure_dir(out_dir)

    working_photo_dir = args.photo_dir

    print("Scanning photos…")
    photos = scan_photos(working_photo_dir)
    if not photos:
        print("No photos found.")
        return

    print("Clustering events…")
    events = cluster_events(
        photos,
        time_gap_hours=args.time_gap_hours,
        distance_gap_km=args.distance_gap_km,
        min_event_size=args.min_event_size,
    )

    if not events:
        print("No events found with current thresholds.")
        return

    print(f"Found {len(events)} events")

    for ev in events:
        print(f"Processing event {ev.event_id} with {len(ev.photo_ids)} photos…")
        selected = ev.photos[: args.max_photos_per_event]

        photo_jsons: List[PhotoJSON] = []
        for p in tqdm(selected, desc=f"VLM per-photo {ev.event_id}"):
            cache_path = os.path.join(cache_dir, f"{p.photo_id}.json")
            if os.path.exists(cache_path) and not args.recompute:
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    pj = PhotoJSON(
                        photo_id=data["photo_id"],
                        caption=data.get("caption", ""),
                        objects=data.get("objects", []),
                        scene_tags=data.get("scene_tags", []),
                        people_present=bool(data.get("people_present", False)),
                        num_people=int(data.get("num_people", 0)),
                        vibe_words=data.get("vibe_words", []),
                        possible_event=data.get("possible_event"),
                    )
                    photo_jsons.append(pj)
                    continue
                except Exception:
                    pass
            try:
                pj = infer_photo_json(args.model, p.filepath, p.photo_id, temperature=args.temperature)
                photo_jsons.append(pj)
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(pj.__dict__, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Failed on {p.filepath}: {e}")

        agg = build_event_aggregate(ev, photo_jsons)

        date_range = _date_range_text(ev.start_time, ev.end_time)
        photo_items = [
            {
                "photo_id": pj.photo_id,
                "caption": pj.caption,
                "objects": pj.objects,
                "scene_tags": pj.scene_tags,
                "people_present": pj.people_present,
                "num_people": pj.num_people,
                "vibe_words": pj.vibe_words,
                "possible_event": pj.possible_event,
            }
            for pj in photo_jsons
        ]

        print("Generating event story…")
        story = infer_event_story(
            model=args.model,
            date_range=date_range,
            location_text=agg.location_text or "",
            uniq_objects=agg.uniq_objects,
            uniq_scene_tags=agg.uniq_scene_tags,
            uniq_vibe_words=agg.uniq_vibe_words,
            photo_items=photo_items[:40],
            temperature=max(0.2, min(0.6, args.temperature + 0.05)),
        )

        print("Extracting palette…")
        palette = dominant_palette([p.filepath for p in selected], k=5)

        print("Rendering storybook…")
        from .render import render_event_storybook

        out_path = render_event_storybook(out_dir, agg, story, palette)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
