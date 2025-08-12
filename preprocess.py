
from PIL import Image
import numpy as np
import cv2

def _to_cv(img: Image.Image):
    arr = np.array(img)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def extract_price_panel(img: Image.Image):
    """Very rough heuristic: crop top 75% as the 'price' area (Robinhood-like)."""
    w, h = img.size
    top = 0
    bottom = int(h * 0.75)
    return img.crop((0, top, w, bottom))

def estimate_trend_slope(price_img: Image.Image) -> float:
    """Estimate trend slope from edges (pixels per 100px width). + up, - down."""
    cv = _to_cv(price_img)
    gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(gray, 50, 150)

    # Collapse edges into a centerline by averaging x for each row
    h, w = edges.shape
    ys = []
    xs = []
    for y in range(h):
        xs_row = np.where(edges[y] > 0)[0]
        if xs_row.size > 0:
            xs.append(xs_row.mean())
            ys.append(y)
    if len(xs) < 10:
        return 0.0

    # Fit line x = a*y + b, then convert to dy/dx slope
    xs = np.array(xs)
    ys = np.array(ys)
    A = np.vstack([ys, np.ones_like(ys)]).T
    a, b = np.linalg.lstsq(A, xs, rcond=None)[0]
    # slope in pixel space: dy/dx ~ 1/a. We want vertical slope sign; invert sign
    if a == 0:
        return 0.0
    slope = -1.0 / a
    # Normalize to width=100px scale
    norm = (w / 100.0) if w>0 else 1.0
    return float(slope / norm)

def detect_sr_levels(price_img: Image.Image, top_k=4):
    """Detect candidate horizontal lines (S/R) using Hough; return row indices (relative)."""
    cv = _to_cv(price_img)
    gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=40, maxLineGap=5)
    if lines is None:
        return []

    h = gray.shape[0]
    rows = []
    for l in lines[:,0,:]:
        x1,y1,x2,y2 = l
        if abs(y2 - y1) <= 2 and abs(x2 - x1) > 20:  # horizontal-ish and long-ish
            rows.append(int((y1+y2)//2))

    if not rows:
        return []

    # cluster rows into unique levels
    rows = np.array(sorted(rows))
    clustered = []
    tol = 6
    cur_cluster = [rows[0]]
    for r in rows[1:]:
        if abs(r - cur_cluster[-1]) <= tol:
            cur_cluster.append(r)
        else:
            clustered.append(int(np.mean(cur_cluster)))
            cur_cluster = [r]
    clustered.append(int(np.mean(cur_cluster)))
    # convert to relative (0..1) from bottom (price uses inverted y)
    levels = []
    for y in clustered:
        rel = 1.0 - (y / float(h))
        levels.append(round(rel, 3))
    # Sort by proximity to current price area (middle-high region tends to matter)
    levels = sorted(levels, reverse=True)[:top_k]
    return levels
