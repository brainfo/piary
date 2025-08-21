from __future__ import annotations

from typing import List, Tuple
import random
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


def _sample_pixels(image_path: str, max_samples: int = 5000) -> np.ndarray:
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        w, h = img.size
        scale = max(1, int(max(w, h) / 512))
        if scale > 1:
            img = img.resize((w // scale, h // scale))
        arr = np.array(img).reshape(-1, 3)
        if arr.shape[0] > max_samples:
            idx = np.random.choice(arr.shape[0], size=max_samples, replace=False)
            arr = arr[idx]
        return arr.astype(np.float32)


def rgb_to_hex(rgb: Tuple[float, float, float]) -> str:
    r, g, b = [max(0, min(255, int(round(c)))) for c in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"


def dominant_palette(image_paths: List[str], k: int = 5, samples_per_image: int = 5000) -> List[str]:
    samples: List[np.ndarray] = []
    for p in image_paths:
        try:
            samples.append(_sample_pixels(p, max_samples=samples_per_image))
        except Exception:
            continue
    if not samples:
        return ["#777777", "#aaaaaa", "#333333"]

    X = np.vstack(samples)
    k = max(1, min(k, 8))
    km = KMeans(n_clusters=k, n_init=4, random_state=0)
    labels = km.fit_predict(X)

    counts = np.bincount(labels)
    centers = km.cluster_centers_.astype(float)

    order = np.argsort(-counts)
    palette = [rgb_to_hex(tuple(centers[i])) for i in order]
    return palette
