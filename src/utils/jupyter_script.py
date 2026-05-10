from pathlib import Path
import json

#simple script to extract the programming language for Jupyter Notebook and remove Jupyter Notebook without codes

input_folder = Path("/workspace/alfred/github_scraping/data/raw")
output_folder = Path("/workspace/alfred/github_scraping/data/jupyter_notebook_processed")
logfile_path = Path("/workspace/alfred/github_scraping/data/jupyter_notebook_processed/jupyter_script_error_logs.txt")
months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november","december"]

#get jupyter programming language and update the jsonl
def get_jupyter_language(jsonl_path:Path, month:str):
    line_counter = 0
    filename = jsonl_path.stem
    output_path = output_folder/month/f"{filename}.jsonl"
    with open(jsonl_path, "r", encoding="utf-8") as f_in: #read and process the raw jsonl file first
        with open(output_path, "a", encoding="utf-8") as f_out: #create a new jsonl file to store the updated data
            with open(logfile_path, "a", encoding="utf-8") as logfile:
                for line in f_in:
                    line_counter +=1
                    if not line.strip(): continue

                    data = json.loads(line)

                    #Only process the files that are Jupyter Notebook
                    if data["language"] == "Jupyter Notebook": 
                        raw_data = data.get("text", "") #Get the metadata of the the Jupyter Notebook
                        #Remove the entire line if the "text" is empty
                        if not raw_data.strip():continue

                        #Load the Jupyter Notebook text into a json and extract the metadata portion
                        try:
                            notebook = json.loads(raw_data)
                            metadata = notebook.get("metadata",{})
                            kernelspec = notebook.get("kernelspec", {})
                            code = get_jupyter_code(notebook)
                            if code is None: continue #skip files with empty code = empty text field
                            data["text"] = code

                            if "language_info" in metadata: #extract the language of the notebook
                                jn_language = metadata.get("language_info", {}).get("name","Unknown").capitalize()
                                data["language"] = jn_language
                                f_out.write(json.dumps(data,ensure_ascii=False) + "\n")
                                continue
                            
                            elif "language" in kernelspec:
                                jn_language = kernelspec.get("language", "Unknown").capitalize()
                                data["language"] = jn_language
                                f_out.write(json.dumps(data,ensure_ascii=False) + "\n")
                                continue                          
                            
                            elif "name" in kernelspec:
                                jn_language = kernelspec.get("name", "Unknown").capitalize()
                                data["language"] = jn_language
                                logfile.write(f"Jupyter Notebook used 'name' field in kernelspec to get the language, please recheck - {line_counter} in {month}/{filename}!\n")
                                f_out.write(json.dumps(data,ensure_ascii=False) + "\n")
                                continue  
                            else:#no language information
                                logfile.write(f"Do not have language_info - {line_counter} in {month}/{filename}, skipped\n")
                                continue

                        except json.JSONDecodeError as e: #malform jsonl in the "text" field -> likely notebook is already corrupted in github -> log out to double check
                            logfile.write(f"Skipping JSONL line {line_counter} in {month}/{filename} due to malformed notebook JSON in 'text' -> {e}\n")
                            continue

                    else: #files that are not Jupyter Notebook, no further changes;just write into the new jsonl file
                        f_out.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"Finished processing on {month}/{jsonl_path.stem}")

empty_code = 0 #testing

#strip jupyter magics/shell escapes; clean up the code by removing unnecessary characters like "%" ,"%%", "!"
def clean_jupyter_code(code: str):
    cleaned_lines = []
    for line in code.splitlines():
        s = line.lstrip()
        if s.startswith("%") or s.startswith("%%") or s.startswith("!"): continue

        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)

#Extract all the codes and update the "text" field
def get_jupyter_code(jupyter_notebook):
    global empty_code
    code_blocks = []
    for cell in jupyter_notebook.get("cells",[]): 
        if cell.get("cell_type") == "code": #find all cells with source code
            src = cell.get("source","")
            if isinstance(src, list):
                cell_code = "".join(src)
            else:
                cell_code = str(src)

            clean_code = clean_jupyter_code(cell_code)
            if clean_code.strip(): code_blocks.append(clean_code) #extract the source code
        
    code = "\n".join(code_blocks) #combine the entire source code together
    if not code.strip(): 
        empty_code+=1 #testing purposes
        return None
    return code


for month in months:
    out_dir = Path(output_folder)/month
    out_dir.mkdir(parents=True, exist_ok=True)
    empty_code = 0
    if month == "september": break
    for jsonl_path in (input_folder/month).glob("output_*.jsonl"):
        print(f"Processing file: {month}/{jsonl_path.stem}")
        get_jupyter_language(jsonl_path, month)
    
    print(f"Total empty code removed for {month}: {empty_code}")
    

print("January-August Jupyter Notebook Script has been processed!")#testing purposes
