#Deduplication
from nemo_curator import ExactDuplicates, AddId, FuzzyDuplicates, FuzzyDuplicatesConfig
from nemo_curator.datasets import DocumentDataset
from gpu_config import start_gpu_cluster
import multiprocessing as mp

#Add Unique ID if needed
add_id = AddId(id_field="my_id", id_prefix="doc_prefix")
#dataset = DocumentDataset.read_json("/workspace/alfred/github_scraping/data/test/january/output_2.jsonl", backend="cudf")


#Dedup configuration
#Exact Deduplicate setup
exact_duplicates = ExactDuplicates(
    id_field="my_id",
    text_field="text",
    hash_method="md5",
    perform_removal=True,
    cache_dir="/content/exact_dedup_outputs",
)


#Fuzzy Deduplicate Setup
config = FuzzyDuplicatesConfig(
    cache_dir="/content/fuzzy_dedup_outputs",
    id_field="my_id",
    text_field="text",
    perform_removal=False,
    seed=42,
    char_ngrams=24,
    num_buckets=20,
    hashes_per_bucket=13,
    use_64_bit_hash=False,
    false_positive_check=False
)

#perform deduplication exact+fuzzy together
def deduplication(dataset):
  dataset_modified = add_id(dataset)
  fuzzy_duplicates = FuzzyDuplicates(config)

  #perform exact dedup first - remove exact duplicates
  exact_deduplicated_dataset = exact_duplicates(dataset_modified)

  #identify fuzzy deduplicates then remove them
  identified_fuzzy_duplicates = fuzzy_duplicates.identify_duplicates(exact_deduplicated_dataset)

  if identified_fuzzy_duplicates is not None:
    deduplicated_dataset = fuzzy_duplicates.remove(exact_deduplicated_dataset, identified_fuzzy_duplicates)
  else:
    print("No fuzzy duplicates found")
    deduplicated_dataset = exact_deduplicated_dataset

  return deduplicated_dataset




  #deduplicated_dataset.to_json("/workspace/alfred/github_scraping/data/filtered/output_test_2_deduped.jsonl")

'''
if __name__ == "__main__":  
  #mp.set_start_method("spawn", force=True)
  dataset = DocumentDataset.read_json("/workspace/alfred/github_scraping/data/test/january/output_2.jsonl", backend="cudf")

  client = start_gpu_cluster()

  deduplication(dataset)

  '''