import language_helpers
from pathlib import Path


input_dir = Path("/workspace/alfred/github_scraping/data/backup")
output_dir = Path("/workspace/alfred/github_scraping/data/raw")
months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november","december"]


for month in months:
    print(f"Updating Languages for {month}")
    (output_dir/month).mkdir(parents=True,exist_ok=True)
    input_jsonl_folder = input_dir/month
    for jsonl_path in input_jsonl_folder.glob("*.jsonl"):
        jsonl_name = jsonl_path.stem
        output_path = output_dir/month/f"{jsonl_name}.jsonl"
        language_helpers.update_jsonl_language(jsonl_path, output_path)
        


