import json
from pathlib import Path

def load_seen_counter(path: Path) -> dict:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_seen_counter(path: Path, data: dict):
    # ensure the parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)  # atomic-ish on POSIX

def next_output_index(output_dir: Path) -> int:
    """Find max N in output_N.jsonl and return N+1."""
    max_n = -1
    for p in output_dir.glob("output_*.jsonl"):
        name = p.stem  # output_N
        try:
            n = int(name.split("_")[1])
            if n > max_n:
                max_n = n
        except Exception:
            continue
    return max_n + 1

def load_current_batch(path: Path) -> list:
    """Reload partial batch if present (each line is a JSON record)."""
    if not path.exists():
        return []
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception as e:
        print(f"[warn] Failed to load partial batch: {e}")
        return []
    print(f"[resume] Loaded {len(records)} records from partial batch.")
    return records

def append_to_current_batch(path: Path, records: list):
    """Append records to partial batch file (line-delimited JSON)."""
    if not records:
        return
    with open(path, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def finalize_batch(output_dir: Path, batch_path: Path, output_index: int) -> int:
    """Rename the partial batch to a final output_{N}.jsonl and return next index."""
    final_path = output_dir / f"output_{output_index}.jsonl"
    if batch_path.exists():
        batch_path.replace(final_path)
        print(f"[✓] Wrote {final_path}")
        return output_index + 1
    return output_index

def get_unique_repos_from_jsonl(path: Path) -> set:
    repos = set()
    if not path.exists():
        return repos
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    rn = obj.get("repo_name")
                    if rn:
                        repos.add(rn)
                except Exception:
                    continue
        print(f"[resume] Current batch already contains {len(repos)} unique repos.")
    except Exception as e:
        print(f"[warn] Failed to seed unique repos from partial batch: {e}")
    return repos