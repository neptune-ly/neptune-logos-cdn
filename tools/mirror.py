"""Copies the public merchant-logo registry from its origin (logos.neptune.ly) into docs/,
which GitHub Pages serves behind Cloudflare at logos-cdn.neptune.ly.

The origin is the source of truth and holds no credential for this repository: this job pulls.
If the origin is slow or down, the last good copy keeps being served.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

ORIGIN = os.environ.get("ORIGIN", "https://logos.neptune.ly/v1/")
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "v1")
FORCE = os.environ.get("FORCE") == "true"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "neptune-logos-mirror"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> None:
    # A unique query string misses every cache on the way, so this reads the origin itself.
    raw = get(f"{ORIGIN}index.json?mirror={int(time.time())}")
    doc = json.loads(raw)
    merchants = doc.get("merchants")
    if doc.get("schema") != 1 or not isinstance(merchants, list):
        sys.exit("refusing: origin index has an unknown shape")

    index_path = os.path.join(OUT, "index.json")
    current = open(index_path, "rb").read() if os.path.exists(index_path) else None
    if current == raw:
        print("unchanged")
        return
    # A sudden loss of most merchants is far likelier to be an origin fault than staff work.
    before = len(json.loads(current)["merchants"]) if current else 0
    if before >= 10 and len(merchants) < before / 2 and not FORCE:
        sys.exit(f"refusing: merchants {before} -> {len(merchants)}; run with force to accept")

    os.makedirs(os.path.join(OUT, "logo"), exist_ok=True)
    for m in merchants:
        h = m.get("logo", "")
        if not re.fullmatch(r"[a-f0-9]{16}", h):
            sys.exit(f"refusing: bad logo id for {m.get('id')}")
        for size in doc.get("logoSizes", [96, 256]):
            path = os.path.join(OUT, "logo", f"{h}-{size}.webp")
            if os.path.exists(path):
                continue
            data = get(f"{ORIGIN}logo/{h}-{size}.webp")
            if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
                sys.exit(f"refusing: {h}-{size} is not WebP")
            if size == 256 and hashlib.sha256(data).hexdigest()[:16] != h:
                sys.exit(f"refusing: {h}-256 does not match its hash")
            with open(path, "wb") as f:
                f.write(data)

    # The index goes last, so it never names a logo that is not already here.
    with open(index_path + ".tmp", "wb") as f:
        f.write(raw)
    os.replace(index_path + ".tmp", index_path)
    print(f"mirrored {len(merchants)} merchants")


if __name__ == "__main__":
    main()
