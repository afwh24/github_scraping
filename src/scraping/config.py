import os
from pathlib import Path
from dotenv import load_dotenv
from helpers import load_seen_counter
from datetime import datetime,timezone

# === CONFIG ===
BATCH_SIZE = 10
load_dotenv() #load environment var
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_3") #CHANGE/ROTATE ALL 4 AVAILABLE TOKENS FOR PARALLELISM (5000 calls/hr)
if not GITHUB_TOKEN:
   raise RuntimeError("GITHUB_TOKEN not set")

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
IGNORED_GIT_FOLDERS = {".git", "node_modules", "__pycache__", "venv", ".idea"}

#change the month for parallelism
BASE_DIR = Path("/workspace/alfred/github_scraping")
repo_counter_path = Path("/workspace/alfred/github_scraping/data/raw/november/seen_repo.json") 
CLONE_DIR = Path("/workspace/alfred/github_scraping/data/raw/november/cloned_repos") 
OUTPUT_DIR = Path("/workspace/alfred/github_scraping/data/raw/november")

# temp file to persist the current in-progress batch
CURRENT_BATCH_PATH = OUTPUT_DIR / "_current_batch.jsonl"

#SET DATETIME FOR PROGRAM EXECUTION
start_dt = datetime(2025, 11, 1, 0, 0, tzinfo=timezone.utc) #datetime(Year, month, date)
end_dt = datetime(2025, 11, 1, 23, 0, tzinfo=timezone.utc) #inclusive

#Helper to check if repo is seen in other months
def check_repo_processed(repo, current_path: Path) -> bool:

    #Remember to add for october, november, and december too
    all_repos_counter_path = [Path("/workspace/alfred/github_scraping/data/raw/january/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/february/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/march/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/april/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/may/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/june/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/july/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/august/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/september/seen_repo.json"),Path("/workspace/alfred/github_scraping/data/raw/october/seen_repo.json"), Path("/workspace/alfred/github_scraping/data/raw/november/seen_repo.json")]

    for i in all_repos_counter_path:
        if i == current_path: continue #skip current path

        result = load_seen_counter(i)
        if repo in result: return True
    
    return False



