# GitHub Source Code AI Dataset Pipeline

An end-to-end pipeline for collecting, filtering, and curating a large-scale source code dataset from GitHub for LLM training and research, replicating and extending concepts from [The Stack v2](https://huggingface.co/datasets/bigcode/the-stack-v2). Built during a six-month AI Engineer internship at HTX, Singapore's national defence-tech agency. This was the largest project of the internship.

## Scale

- **5.5M+** GitHub repositories processed
- **35M+** source files extracted
- **600GB** of curated JSONL datasets produced
- **~40B** raw tokens

Repository data was collected across all twelve months of 2025, with cross-month deduplication ensuring no repository was collected more than once across the full year-long effort.

## Pipeline overview

### 1. Repository discovery (`gharchive.py`)
Repository candidates are discovered by streaming [GH Archive](https://www.gharchive.org/) hourly event logs, filtering specifically for `PushEvent` and `CreateEvent` types.

### 2. Metadata enrichment and filtering (`github_helpers.py`)
Each candidate repository is enriched via the GitHub REST API, accessed directly via `requests` (not a wrapper library, for finer-grained control over pagination, rate limits, and error handling). Four personal access tokens are rotated to increase the effective API throughput.

Each repository must pass all of the following filters:
- Minimum 50 GitHub stars
- Repository size between approximately 50MB and 1GB
- A supported programming language (see below)
- A valid default branch

### 3. Language filtering (`constants.py`, `language_helpers.py`)
Rather than maintaining an inclusion list, the pipeline maintains an **exclusion list** of languages and file extensions considered unsuitable for code LLM training, following the methodology described in the Stack v2 paper. Excluded categories include non-code data formats (CSV, TSV, SVG, Diff files), CAD/3D formats, and a small number of specific languages excluded for relevance, including Go. A separate extension-based exclusion list filters out configuration files, lock files, and other non-source-code file types regardless of detected language.

### 4. Cloning (`github_helpers.py`)
Repositories are cloned using **shallow clones** (`git clone --depth 1`) of the default branch only, to minimise bandwidth and storage. Large or irrelevant directories (`.git`, `node_modules`, `__pycache__`, virtual environments, IDE config folders) are excluded from scanning.

### 5. Jupyter Notebook handling (`jupyter_script.py`)
Notebooks (`.ipynb`) are stored as JSON, not plain text, and require special handling:
- Code cells are extracted; markdown and empty cells are discarded
- Notebook-specific syntax (magic commands, shell escapes) is stripped from extracted code
- Programming language is determined via a three-tier fallback: `metadata.language_info`, then `kernelspec.language`, then `kernelspec.name` (logged for review if this last, less reliable tier is used)
- Notebooks with no extractable code or malformed JSON structure are skipped and logged rather than crashing the pipeline

### 6. Quality filtering (`filter.py`, using NVIDIA NeMo Curator)
Five filters are applied: line-of-code bounds, alphabetic character ratio, XML header detection, HTML boilerplate detection, and tokenizer fertility (using a Codestral-22B tokenizer for this experiment). A regex-based pre-filter excludes malformed HTML before the HTML boilerplate filter runs. If the full filtering chain fails (commonly on malformed HTML), the pipeline falls back to running all filters except HTML filtering rather than losing the batch.

### 7. Deduplication (`dedup.py`, using NVIDIA NeMo Curator)
Both **exact** (content hashing) and **fuzzy** (character n-gram similarity) deduplication are applied, reducing memorisation risk from near-duplicate content that exact hashing alone would miss.

## Resilience and infrastructure

- Repository-level checkpointing and resume — interrupted runs pick up without reprocessing completed repositories
- Cross-month duplicate checking across the full twelve-month collection effort
- Per-file character encoding detection (via `chardet`), falling back to UTF-8
- GPU-accelerated filtering with CPU fallback when CUDA/cuDF/CuPy environment configuration could not be reliably established

## Output schema

Each record in the final JSONL dataset contains:

```json
{
  "repo_name": "owner/repo",
  "description": "...",
  "stars": 1234,
  "file_count": 56,
  "size_kb": 75000,
  "language": "Python",
  "license": "mit",
  "file_name": "src/main.py",
  "text": "...extracted source code..."
}
```

## Tech stack

Python, GitHub REST API, GH Archive, NVIDIA NeMo Curator, Dask, cuDF/CuPy (GPU-accelerated dataframes), JSONL
