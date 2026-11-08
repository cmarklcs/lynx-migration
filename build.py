"""Lynx Journeys: combine data/*.json into site/topics.json, copy images, fetch video thumbnails,
and record read-aloud audio with the Mac's System voice (set to Siri)."""
import hashlib, json, os, pathlib, re, shutil, subprocess, urllib.request

ROOT = pathlib.Path(__file__).parent
SITE = ROOT / "site"
for d in ("images", "thumbs", "audio"):
    (SITE / d).mkdir(parents=True, exist_ok=True)

topics, problems = [], []
for f in sorted((ROOT / "data").glob("*.json")):
    t = json.loads(f.read_text())
    for p in t["photos"]:
        src = ROOT / "images" / p["file"]
        if src.exists():
            shutil.copy(src, SITE / "images" / p["file"])
        else:
            problems.append(f"{t['slug']}: missing image {p['file']}")
    for v in t["videos"]:
        m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", v["url"])
        if not m:
            problems.append(f"{t['slug']}: bad video url {v['url']}")
            continue
        out = SITE / "thumbs" / f"{m.group(1)}.jpg"
        if not out.exists():
            try:
                urllib.request.urlretrieve(f"https://i.ytimg.com/vi/{m.group(1)}/hqdefault.jpg", out)
                subprocess.run(["sips", "-s", "formatOptions", "70", "-Z", "640", str(out)], capture_output=True)
            except Exception as e:
                problems.append(f"{t['slug']}: thumbnail failed {e}")
        if out.exists():
            v["thumb"] = out.name
    for s in t["sections"]:
        for i in s.get("from", []):
            if i >= len(t["sources"]):
                problems.append(f"{t['slug']}: section {s['key']} cites missing source {i}")
    books = ROOT / "data" / "books" / f.name
    t["books"] = json.loads(books.read_text()).get("books", []) if books.exists() else []
    topics.append(t)

topics.sort(key=lambda t: t.get("startYear", 0))

# ---- read-aloud recordings: one per paragraph, intro, and vocabulary entry ----
VOICE = os.environ.get("VOICE", "system")
RATE = os.environ.get("RATE", "175")

def texts(t):
    yield t["intro"]
    for s in t["sections"]:
        yield from s["paragraphs"]
    for v in t["vocab"]:
        yield v["word"]
        yield v["meaning"]

made = 0
for t in topics:
    t["audio"] = {}
    for text in texts(t):
        name = hashlib.sha1(f"{VOICE}|siri-nora|{RATE}|{text}".encode()).hexdigest()[:14] + ".m4a"
        out = SITE / "audio" / name
        if not out.exists():
            for attempt in range(3):
                try:
                    subprocess.run(["say", *([] if VOICE == "system" else ["-v", VOICE]), "-r", RATE, "--file-format=m4af",
                                    "--data-format=aac@22050", "--channels=1", "--bit-rate=32000",
                                    "-o", str(out), text], check=True, timeout=90)
                    made += 1
                    break
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    subprocess.run(["pkill", "-x", "say"])
                    out.unlink(missing_ok=True)
            else:
                problems.append(f"{t['slug']}: could not record {text[:50]!r}")
        if out.exists():
            t["audio"][text] = name

(SITE / "topics.json").write_text(json.dumps(topics, ensure_ascii=False))
print(f"audio: {made} new recordings")
print(f"{len(topics)} topics built")
print("\n".join(problems) or "no problems")
