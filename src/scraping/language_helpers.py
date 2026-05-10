import json
from pathlib import Path
from constants import excluded_programming_languages

language_path = "/workspace/alfred/github_scraping/languages.json"

with open(language_path, "r", encoding="utf-8") as f: 
    LANGUAGES = json.load(f)

ALL_EXTENSIONS = set()

#remove the excluded programming languages first
for excluded_language in excluded_programming_languages:
    LANGUAGES.pop(excluded_language,None) #pop if it exists, else nothing happens

for extension_list in LANGUAGES.values():
    for ext in extension_list:
        ALL_EXTENSIONS.add(ext)


#Reverse map to get the language
def load_ext_to_lang() -> dict[str, str]:

    ext_to_lang = {}

    for lang, tokens in LANGUAGES.items():
        for tok in tokens or []:
            if isinstance(tok,str) and tok.startswith("."):
                ext_to_lang[tok.lower()] = lang
    
    return ext_to_lang



ext_to_lang = load_ext_to_lang()

#Detect the language
def detect_language(file_path:str) -> str:
    if not file_path: return "Unknown"

    ext = Path(file_path).suffix.lower()
    return ext_to_lang.get(ext, "Unknown")



#Detect the language for each line in jsonl and update in the jsonl file (can be deleted once all scraping data has been updated)
def update_jsonl_language(jsonl_path:Path, output_path:Path):
    #ext = load_ext_to_lang()
    with open(jsonl_path, "r", encoding="utf-8") as f_in:
        with open(output_path, "a", encoding="utf-8") as f_out:
            for line in f_in:
                if not line.strip(): continue

                data = json.loads(line)
                file_name = data.get("file_name")
                language_detected = detect_language(file_name)
                data["language"]  = language_detected
                f_out.write(json.dumps(data, ensure_ascii=False) + "\n")

    #print("Language detection completed!")




