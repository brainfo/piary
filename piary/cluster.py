from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
import math

from .types import PhotoIndex, Event


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _distance_km(a: PhotoIndex, b: PhotoIndex) -> Optional[float]:
    if a.lat is None or a.lon is None or b.lat is None or b.lon is None:
        return None
    return _haversine_km(a.lat, a.lon, b.lat, b.lon)


def _cluster_center_lat_lon(photos: List[PhotoIndex]) -> Tuple[Optional[float], Optional[float]]:
    vals = [(p.lat, p.lon) for p in photos if p.lat is not None and p.lon is not None]
    if not vals:
        return None, None
    lat = sum(v[0] for v in vals) / len(vals)
    lon = sum(v[1] for v in vals) / len(vals)
    return lat, lon


def cluster_events(
    photos: List[PhotoIndex],
    time_gap_hours: float = 6.0,
    distance_gap_km: float = 80.0,
    min_event_size: int = 3,
) -> List[Event]:
    if not photos:
        return []

    events: List[Event] = []
    current: List[PhotoIndex] = []
    threshold_seconds = time_gap_hours * 3600.0

    for p in photos:
        if not current:
            current.append(p)
            continue
        prev = current[-1]

        time_ok = True
        if prev.datetime and p.datetime:
            delta = (p.datetime - prev.datetime).total_seconds()
            time_ok = delta <= threshold_seconds

        dist_ok = True
        dist = _distance_km(prev, p)
        if dist is not None:
            dist_ok = dist <= distance_gap_km

        if time_ok and dist_ok:
            current.append(p)
        else:
            if len(current) >= min_event_size:
                events.append(_finalize_event(current, len(events)))
            current = [p]

    if current:
        if len(current) >= min_event_size:
            events.append(_finalize_event(current, len(events)))

    return events


def _finalize_event(photos: List[PhotoIndex], idx: int) -> Event:
    start_time = min((p.datetime for p in photos if p.datetime), default=None)
    end_time = max((p.datetime for p in photos if p.datetime), default=None)
    lat, lon = _cluster_center_lat_lon(photos)
    event_id = f"E{idx+1:04d}"
    return Event(
        event_id=event_id,
        photo_ids=[p.photo_id for p in photos],
        start_time=start_time,
        end_time=end_time,
        center_lat=lat,
        center_lon=lon,
        photos=photos,
    )
