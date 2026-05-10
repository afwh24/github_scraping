import io
import json
import gzip
import requests
from datetime import timedelta

#Iterate each GH archive logs url by the hour of each day
def iterate_gharchive_urls(start_date, end_date):
    dt = start_date
    while dt <= end_date:
        yield f"https://data.gharchive.org/{dt.strftime('%Y-%m-%d-%-H')}.json.gz"
        dt += timedelta(hours=1)

#Request the json logs file
def stream_repos_from_gharchive(start_date, end_date, max_repos=None):
    seen = {}
    for i, url in enumerate(iterate_gharchive_urls(start_date, end_date), 1):
        print(f"[{i}] Fetching GH Archive: {url}")
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                print(f"[!] Skipped (status {r.status_code}): {url}")
                continue
            with gzip.open(io.BytesIO(r.content), "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event["type"] not in ("PushEvent", "CreateEvent"):
                            continue
                        repo_name = event["repo"]["name"]
                        created_at = event.get("created_at")
                        if repo_name not in seen or seen[repo_name] < created_at:
                            seen[repo_name] = created_at
                        if max_repos is not None and len(seen) >= max_repos:
                            return list(seen.keys())
                    except:
                        continue
        except Exception as e:
            print(f"[!] Failed to fetch {url}: {e}")
            continue
    return list(seen.keys())