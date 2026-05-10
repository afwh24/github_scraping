from config import input_dir,output_filtered_dir,output_deduped_dir,deduped_pandas_meta, cudf_meta
from pathlib import Path
import nemo_curator as nc
from nemo_curator.datasets import DocumentDataset
from filter import loc_filter, alpha_filter, xml_filter, HTML_filter,all_filters, token_fertility_filter
from dedup import deduplication
from gpu_config import start_gpu_cluster
import dask.dataframe as dd
import os
import dask_cudf
import cudf


months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november","december"]
logfile_path = Path("/workspace/alfred/github_scraping/filter_error_logs.txt")


if __name__ == "__main__":
    #start gpu
    client = start_gpu_cluster(gpu="7")

    #Deduplication and filtering process for each month
    for month in months:
        input_jsonl_folder = input_dir/month #contains all the jupyter-processed jsonl

        #create the respective month folder
        output_filtered_folder = output_filtered_dir/month
        output_deduped_folder = output_deduped_dir/month
        output_filtered_folder.mkdir(parents=True, exist_ok=True)
        output_deduped_folder.mkdir(parents=True, exist_ok=True)

        for jsonl_path in input_jsonl_folder.glob("output*.jsonl"):
                jsonl_file = jsonl_path.stem
                deduped_jsonl_file_path = output_deduped_folder/f"{jsonl_file}_deduped.jsonl"
                filtered_jsonl_file_path = output_filtered_folder/f"{jsonl_file}_filtered.jsonl"
                print(f"[Info] Processing {jsonl_file}")
                #filtered file exist -> deduplication and filtering completed; skipped
                if filtered_jsonl_file_path.exists():
                     print(f"[Skipped] {filtered_jsonl_file_path} already exist!")
                     continue
                
                #deduped file not exist -> havent deduplication and filter yet
                if not deduped_jsonl_file_path.exists():    
                    #dataset = DocumentDataset.read_json(str(jsonl_path), backend="cudf")
                    df = dd.read_json(str(jsonl_path), lines=True)
                    gdf = df.map_partitions(lambda pdf: cudf.DataFrame.from_pandas(pdf))
                    dataset = DocumentDataset(gdf)
                    
                    print(f"[Deduplication] Deduplicating {jsonl_file}")

                    #perform deduplication
                    deduped_dataset = deduplication(dataset)
                    deduped_dataset.repartition(npartitions=1).to_json(str(deduped_jsonl_file_path))
                    print(f"[Deduplication] Deduplicated dataset has been saved to {deduped_jsonl_file_path}")

                else:
                     print(f"[Deduplication] Skipped deduplication, proceeding to data filtering")

                #Then perform data curation/filtering
                ddf = dd.read_json(str(deduped_jsonl_file_path), lines=True, meta=deduped_pandas_meta)
                dataset = DocumentDataset(ddf)
                print(f"[Filter] Filtering {deduped_jsonl_file_path}")
                filtered_dataset = all_filters(dataset)

                try:
                    filtered_dataset.repartition(npartitions=1).to_json(str(filtered_jsonl_file_path))
                    print(f"[Filter] Filtered dataset has been saved to {filtered_jsonl_file_path}")

                except Exception as e:
                    print(f"[Error] HTML filtering pipeline failed")
                    with open(logfile_path, "a", encoding="utf-8") as f:
                        f.write(f"{input_jsonl_folder}/{jsonl_file} -> HTML filtering pipeline failed: {e}\n")

                    #Perform NeMo-Curator LOC, Alpha, XML, token fertility filtering only
                    try:
                        print(f"[Filter] Perform data filtering without HTML filtering pipeline")
                        loc_filtered_ds = loc_filter(dataset)
                        loc_alpha_filtered_ds = alpha_filter(loc_filtered_ds)
                        loc_alpha_xml_filtered_ds = xml_filter(loc_alpha_filtered_ds)
                        filtered_dataset = token_fertility_filter(loc_alpha_xml_filtered_ds)
                        filtered_dataset.repartition(npartitions=1).to_json(str(filtered_jsonl_file_path))
                        print(f"[Filter] Filtered dataset has been saved to {filtered_jsonl_file_path} without HTML")

                    except Exception as e2:
                        with open(logfile_path, "a", encoding="utf-8") as f:
                            f.write(f"{input_jsonl_folder}/{jsonl_file} -> Data filtering pipeline failed: {e2}\n")
                        raise

        #break #only perform for the month



