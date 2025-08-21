from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict

from .types import PhotoIndex
from .exif_utils import extract_time_and_gps


_SUPPORTED_EXTS = {".jpg", ".jpeg", ".png"}


def _is_image(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in _SUPPORTED_EXTS


def scan_photos(photo_dir: str) -> List[PhotoIndex]:
    photo_paths: List[str] = []
    for root, _, files in os.walk(photo_dir):
        for f in files:
            p = os.path.join(root, f)
            if _is_image(p):
                photo_paths.append(p)

    photo_ids_seen: Dict[str, int] = {}
    results: List[PhotoIndex] = []

    for path in sorted(photo_paths):
        base = os.path.basename(path)
        photo_id = base
        if photo_id in photo_ids_seen:
            photo_ids_seen[photo_id] += 1
            stem, ext = os.path.splitext(base)
            photo_id = f"{stem}_{photo_ids_seen[base]}{ext}"
        else:
            photo_ids_seen[photo_id] = 0

        dt, lat, lon = extract_time_and_gps(path)
        if dt is None:
            try:
                mtime = os.path.getmtime(path)
                dt = datetime.fromtimestamp(mtime)
            except Exception:
                dt = None

        results.append(PhotoIndex(photo_id=photo_id, filepath=path, datetime=dt, lat=lat, lon=lon))

    results.sort(key=lambda p: p.datetime or datetime.min)
    return results
