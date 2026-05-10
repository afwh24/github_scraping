from pathlib import Path
import shutil
from pygments.lexers import get_all_lexers
import pandas as pd

#configuration setup for data curation/filtering

#input_dir = Path("/workspace/alfred/github_scraping/data/jupyter_notebook_processed") #after processed by jupyter script; can be changed afterwards, temp folder for testing
input_dir = Path("/workspace/alfred/github_scraping/data/jupyter_notebook_processed") #after processed by jupyter script; to be changed to jupyter_notebook_processed once everything is ok
output_filtered_dir = Path("/workspace/alfred/github_scraping/data/filtered")  #to store all filtered (and deduped) jsonl files; final output
output_deduped_dir = Path("/workspace/alfred/github_scraping/data/deduped") #to store all deduped jsonl, can be deleted after all files have been filtered
tokenizer_model_path = "/workspace/alfred/github_scraping/sp_tokenizer/tokenizer.model"

#create base folder if it doesnt exist yet
if not output_filtered_dir.exists(): output_filtered_dir.mkdir(parents=True, exist_ok=True)
if not output_deduped_dir.exists(): output_deduped_dir.mkdir(parents=True, exist_ok=True)

deduped_pandas_meta = pd.DataFrame({
    "repo_name": pd.Series(dtype="object"),
    "description": pd.Series(dtype="object"),
    "stars": pd.Series(dtype="Int64"),  
    "file_count": pd.Series(dtype="Int64"),
    "size_kb": pd.Series(dtype="Int64"),
    "language": pd.Series(dtype="object"),
    "license": pd.Series(dtype="object"),
    "file_name": pd.Series(dtype="object"),
    "text": pd.Series(dtype="object"),
    'my_id': pd.Series(dtype="object")
})

cudf_meta = pd.DataFrame({
    "description": pd.Series(dtype="object"),
    "file_count": pd.Series(dtype="Int64"),
    "file_name": pd.Series(dtype="object"),
    "language": pd.Series(dtype="object"),
    "license": pd.Series(dtype="object"),
    "repo_name": pd.Series(dtype="object"),
    "size_kb": pd.Series(dtype="Int64"),
    "stars": pd.Series(dtype="Int64"),  
    "text": pd.Series(dtype="object")
})

# Language → MIME mapping for GeneralCommentToCodeFilter
LANGUAGES_TO_MIME = {}
for lexer in get_all_lexers():
    name, aliases, filetypes, mimetypes = lexer
    if mimetypes:
        # keep the first MIME type if multiple exist
        LANGUAGES_TO_MIME[name.lower()] = mimetypes[0]

#HARDCODED MIME THAT ARE NOT IN LEXERS
hardcoded_mime = {
    "shell": "text/x-sh",
    "r": "text/x-r",
    "objective c": "text/x-objectivec",
    "objective c++": "text/x-objectivec++",
    "fsharp": "text/x-fsharp",
    "lisp": "text/x-common-lisp",
}

