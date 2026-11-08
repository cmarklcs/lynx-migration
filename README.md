# Lynx Journeys

4th grade migration research library for Lausanne Collegiate School: grade-level reports, timelines, maps,
photos, videos, Epic books, Britannica School links, and citable sources for 15 events that caused people to move.

- `data/<topic>.json`: page content, sources, videos, and image credits
- `data/books/<topic>.json`: Epic book suggestions
- `images/`: images from Wikimedia Commons, credited on each page
- `build.py`: run `python3 build.py` to rebuild `site/` and record read-aloud audio. The Mac's System voice must be set to Siri.
- `site/`: the published website. GitHub Pages deploys this folder on every push to `main`.
- Teacher settings (`site/admin.html`) use the shared Lynx settings server, with site "journeys" and its own password.
