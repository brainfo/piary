from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ExifTags


_DATETIME_TAGS = {
    "DateTimeOriginal",
    "DateTimeDigitized",
    "DateTime",
}

_GPS_TAG = "GPSInfo"


def _get_exif(image_path: str) -> dict:
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if not exif:
                return {}
            tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            if _GPS_TAG in tag_map and isinstance(tag_map[_GPS_TAG], dict):
                gps_map = {
                    ExifTags.GPSTAGS.get(k, k): v
                    for k, v in tag_map[_GPS_TAG].items()
                }
                tag_map[_GPS_TAG] = gps_map
            return tag_map
    except Exception:
        return {}


def _parse_datetime(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def _to_deg(value) -> Optional[float]:
    try:
        d = float(value[0][0]) / float(value[0][1])
        m = float(value[1][0]) / float(value[1][1])
        s = float(value[2][0]) / float(value[2][1])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return None


def extract_time_and_gps(image_path: str) -> Tuple[Optional[datetime], Optional[float], Optional[float]]:
    exif = _get_exif(image_path)

    dt: Optional[datetime] = None
    for key in _DATETIME_TAGS:
        if key in exif and isinstance(exif[key], str):
            dt = _parse_datetime(exif[key])
            if dt:
                break

    lat = lon = None
    gps = exif.get(_GPS_TAG)
    if isinstance(gps, dict):
        lat_ref = gps.get("GPSLatitudeRef")
        lon_ref = gps.get("GPSLongitudeRef")
        lat_val = gps.get("GPSLatitude")
        lon_val = gps.get("GPSLongitude")
        if lat_val and lon_val and lat_ref and lon_ref:
            lat = _to_deg(lat_val)
            lon = _to_deg(lon_val)
            if lat is not None and lat_ref in ["S", b"S"]:
                lat = -lat
            if lon is not None and lon_ref in ["W", b"W"]:
                lon = -lon

    return dt, lat, lon
