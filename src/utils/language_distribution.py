import json
from collections import defaultdict, Counter
from pathlib import Path
import csv

#simple script to calculate the statistics summary for the repo metadata

BASE_DIR = Path("/workspace/alfred/github_scraping/data/raw")
months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november","december"]
language_output_csv_path = Path("language.csv")

language_counter = Counter()

language_path = Path("languages.json")

with open(language_path, "r", encoding="utf-8") as f:
    languages = json.load(f)
language_output_csv_path = Path("language.csv")

#Reverse map to get the language
def load_ext_to_lang(languages_path: Path) -> dict[str, str]:
    language_data = json.loads(languages_path.read_text(encoding="utf-8"))

    ext_to_lang = {}

    for lang, tokens in language_data.items():
        for tok in tokens or []:
            if isinstance(tok,str) and tok.startswith("."):
                ext_to_lang[tok.lower()] = lang
    
    return ext_to_lang

#Detect the language
def detect_language(file_path:str, ext_to_lang: dict[str,str]) -> str:
    if not file_path: return "Unknown"

    ext = Path(file_path).suffix.lower()
    return ext_to_lang.get(ext, "Unknown")

def language_stats(folder_path:Path):
    ext_map = load_ext_to_lang(language_path)

    for jsonl_path in folder_path.rglob("output_*.jsonl"):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s: continue

                rec = json.loads(s)
                file_path = rec.get("file_name")
                language = detect_language(file_path, ext_map)
                language_counter[language] +=1

#simple script to calculate language distribution
def language_distribution(language_output_csv_path:Path):
    for month in months:
        folder_path = BASE_DIR/month
        if month == "september": break #sept has no files yet
        language_stats(folder_path)

    #store it in a csv file
    with open(language_output_csv_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Language", "Count"]) #Header
        for lang, count in language_counter.items():
            writer.writerow([lang,count])

    print(f"Completed Language Distribution")

language_distribution(language_output_csv_path)
