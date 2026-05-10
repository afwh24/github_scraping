import os
from transformers import AutoTokenizer
from dotenv import load_dotenv

#download the mistralai codestral model for token fertility filter (nemo-curator)
load_dotenv()
hf_token = os.getenv('HUGGINGFACE_TOKEN')

tok = AutoTokenizer.from_pretrained(
    "mistralai/Codestral-22B-v0.1",
    token=hf_token                                  # modern Transformers
)
tok.save_pretrained("/workspace/alfred/github_scraping/sp_tokenizer")