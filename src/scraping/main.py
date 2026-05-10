
import requests
import shutil
from gharchive import stream_repos_from_gharchive
from helpers import load_seen_counter, save_seen_counter, next_output_index, load_current_batch, append_to_current_batch, finalize_batch, get_unique_repos_from_jsonl
from config import BATCH_SIZE, HEADERS, CLONE_DIR,OUTPUT_DIR, CURRENT_BATCH_PATH, repo_counter_path, start_dt, end_dt, check_repo_processed
from github_helpers import get_repo_metadata, clone_repo, scan_repo

def main():
  OUTPUT_DIR.mkdir(exist_ok=True) 
  CLONE_DIR.mkdir(exist_ok=True)

  try:
    r = requests.get("https://api.github.com/rate_limit", headers=HEADERS, timeout=10)
    if r.ok:
      print("[i] Rate limit:", r.json().get("resources", {}).get("core", {}))
  except Exception:
    pass


  print(f"[+] Starting GH Archive processing from {start_dt} to {end_dt}")
  repos = stream_repos_from_gharchive(start_dt, end_dt)

  # resume seen_repo + output index + partial batch
  repo_counter = load_seen_counter(repo_counter_path)
  output_counter = next_output_index(OUTPUT_DIR)
  repo_batch = load_current_batch(CURRENT_BATCH_PATH)

  repos_in_current_batch = get_unique_repos_from_jsonl(CURRENT_BATCH_PATH)


  for i, repo in enumerate(repos, 1):    
      if repo in repo_counter:  # already processed in a previous run
          print(f"[!] Skipping already seen repo: {repo}")
          continue
      
      repo_exist = check_repo_processed(repo, repo_counter_path)
      if repo_exist:
          print(f"[!] Skipping already seen repo in other month: {repo}")
          continue
      

      meta = get_repo_metadata(repo)
      if not meta:
          # still mark as seen so we dont re-try the same repo forever
          repo_counter[repo] = repo_counter.get(repo, 0) + 1 
          save_seen_counter(repo_counter_path, repo_counter)   
          continue

      try:
          repo_path = clone_repo(meta)
          print(f"[*] Sucessfully cloned: {repo} at {repo_path}")
      except Exception as e:
          print(f"[!] Clone failed for {repo}: {e}")
          repo_counter[repo] = repo_counter.get(repo, 0) + 1   
          save_seen_counter(repo_counter_path, repo_counter)    
          continue

      try:
        records = scan_repo(meta, repo_path)
      except Exception as e:
          print(f"[!] Failed to scan repo {repo}: {e}")
          repo_counter[repo] = repo_counter.get(repo, 0) + 1    
          save_seen_counter(repo_counter_path, repo_counter)    
          continue

      print(f"[✓] Saved metadata for: {repo}")


      if records:
        # add to memory batch
        repo_batch.extend(records)
        # and append immediately to on-disk partial batch (checkpoint)  [ADDED]
        append_to_current_batch(CURRENT_BATCH_PATH, records)

        repos_in_current_batch.add(meta["repo_name"])
        print(f"[stats] Current file has {len(repos_in_current_batch)} repos")

      # mark seen as soon as we successfully got records and appended the data
      repo_counter[repo] = repo_counter.get(repo, 0) + 1       
      save_seen_counter(repo_counter_path, repo_counter)        

      # finalize a batch if big enough
      if len(repos_in_current_batch) >= BATCH_SIZE:
        output_counter = finalize_batch(OUTPUT_DIR, CURRENT_BATCH_PATH, output_counter)  
        repo_batch = []
        repos_in_current_batch.clear()
        shutil.rmtree(CLONE_DIR, ignore_errors=True)
        CLONE_DIR.mkdir(exist_ok=True)

  # ---- Final partial batch (if any): write JSONL + save seen_repo.json ---
  if repo_batch:
      # finalize whatever is in CURRENT_BATCH_PATH
      output_counter = finalize_batch(OUTPUT_DIR, CURRENT_BATCH_PATH, output_counter) 
      repo_batch = []
      repos_in_current_batch.clear()
      save_seen_counter(repo_counter_path, repo_counter)

      #Clean up - delete the folder
      shutil.rmtree(CLONE_DIR, ignore_errors=True)

  print(f"All repos from {start_dt.strftime('%d %B %Y')} to {end_dt.strftime('%d %B %Y')} UTC has been scraped")

if __name__ == "__main__":
    main()
