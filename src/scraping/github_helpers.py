
import requests
import subprocess
import shutil
import chardet
import time
from datetime import datetime, timezone
from constants import excluded_extensions
from config import HEADERS, IGNORED_GIT_FOLDERS, CLONE_DIR
from language_helpers import ALL_EXTENSIONS, LANGUAGES, detect_language

#retrieve repository metadata via github API
def get_repo_metadata(repo):
    url = f"https://api.github.com/repos/{repo}"
    for attempt in range(3): #retry up to 3 times
        try:
            r = requests.get(url, headers=HEADERS)
            if r.status_code == 200: #success
                data = r.json()
                stars = data.get("stargazers_count")
                size = data.get("size")
                language = data.get("language")

                #Process only repos with >= 50 stars
                if stars < 50:
                    print(f"[!] Skipping {repo} due to insufficient stars: {stars}")
                    return None

                #Get files only > 50 MB and < 1GB (size in github api is recorded as kilobytes)
                elif size < 50_000 or size > 1_000_000:
                    print(f"[!] Skipping {repo} due to invalid size : {size} KB")
                    return None

                #Github unable to detect the languages used
                elif language is None:
                    print(f"[!] Skipping {repo} due to language could not be detected")
                    return None

                #language is not recorded in the languages.json file -> invalid/excluded languages
                elif language not in LANGUAGES:
                    print(f"[!] Skipping {repo} due to unsupported language : {language}")
                    return None

                return {
                    "repo_name": repo,
                    "description": data.get("description", "null"),
                    "stars": stars,
                    "default_branch": data.get("default_branch", "main"),
                    "license": (data.get("license") or {}).get("key") or "null",
                    "size": size,
                    "language": language
                }
            elif r.status_code == 403: #API limit hit
                wait_for_rate_limit(HEADERS)
                print(f"[Rate] Failed to connect to {url} due to API limit, retrying... ({attempt+1}/3)")
                continue
            else:
                print(f"[!] Metadata fetch failed for {repo} (status {r.status_code})")
                return None
        except Exception as e:
            print(f"[Connection Error] Failed to connect to {url}, retrying... ({attempt+1}/3)")
            time.sleep((attempt+1)*5) #increase the delay after each fail reattempt
    return None

#Clone the latest main/master branch of the repo only
def clone_repo(meta):
    repo_path = CLONE_DIR / meta["repo_name"].replace("/", "__")
    if repo_path.exists(): 
       shutil.rmtree(repo_path, ignore_errors=True)

    url = f"https://github.com/{meta['repo_name']}.git"
    subprocess.run([
        "git", "clone", "--depth", "1", "--branch", meta["default_branch"], url, str(repo_path)
    ], check=True)
    return repo_path

def is_valid_code_file(path):
  ext = path.suffix.lower()
  return (
        path.is_file()
        and ext in ALL_EXTENSIONS
        and ext not in excluded_extensions
        and not any(part in IGNORED_GIT_FOLDERS for part in path.parts)
    )

def detect_encoding(path):
    try:
        raw = path.read_bytes()[:2048] # read first 2KB of file
        return chardet.detect(raw)["encoding"] or "utf-8"
    except:
        return "utf-8"

#scan the clone repo to get the raw content of the source code
def scan_repo(repo_meta, repo_path):
    valid_files = [f for f in repo_path.rglob("*") if is_valid_code_file(f)]
    records = []

    #Retrieve content for each file in the git clone
    for file_path in valid_files:
        try:
            encoding = detect_encoding(file_path)
            content = file_path.read_text(encoding=encoding, errors="ignore")
            language = detect_language(str(file_path))
            records.append({
                "repo_name": repo_meta["repo_name"],
                "description": repo_meta["description"],
                "stars": repo_meta["stars"],
                "file_count": len(valid_files),
                "size_kb": repo_meta["size"],
                "language": language,
                "license": repo_meta["license"],
                "file_name": str(file_path.relative_to(repo_path)),
                "text": content 
            })


        except Exception as e:
            print(f"[-] Failed reading file {file_path}: {e}")
            continue
    return records

#Github API Rate Limit Guard
def wait_for_rate_limit(headers):
  try:
    r = requests.get("https://api.github.com/rate_limit", headers=headers, timeout=10)
    if not r.ok:
      return

    core = r.json().get("resources", {}).get("core", {})
    remaining = int(core.get("remaining",0) or 0)
    reset_epoch = int(core.get("reset", 0) or 0)

    #no more API calls, wait for reset
    if remaining == 0 and reset_epoch:
      reset_time = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
      now = datetime.now(timezone.utc)
      wait_seconds = max(0, int((reset_time-now).total_seconds())) + 60 # 60 seconds buffer
      mins, secs = divmod(wait_seconds, 60)
      print(f"[Rate] remaining=0; waiting ~{mins}m {secs}s until {reset_time} UTC…")
      time.sleep(wait_seconds)

  except Exception as e:
    print(f"[Rate] Failed to check rate limit: {e}")
