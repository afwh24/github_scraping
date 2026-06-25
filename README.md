# GitHub Source Code AI Dataset Collection and Curation Pipeline

A large-scale GitHub repository scraping, filtering, and dataset curation pipeline designed to collect permissively licensed source code repositories, extract file-level source code and metadata, and prepare high-quality code datasets for AI and LLM training and research.

This project replicates and extends concepts from datasets such as The Stack v2, with a focus on scalability, data quality, and reproducibility.

---

## Overview

The pipeline covers the full dataset preparation workflow from repository discovery through to curated JSONL dataset generation:

- Discovering repositories via GH Archive event streams
- Filtering repositories against predefined quality criteria
- Cloning repositories and extracting source code at scale
- Processing Jupyter Notebooks into clean, training-ready source code
- Applying quality filters and deduplication using NVIDIA NeMo Curator
- Producing structured JSONL datasets for LLM training and research

**Scale achieved:**
- 5.5M+ GitHub repositories processed
- 35M+ source files extracted
- 600GB of curated JSONL code datasets generated
- Approximately 40 billion raw code tokens collected

---

## Pipeline Architecture

### 1. Repository Discovery
- GH Archive event stream scraping to identify active repositories
- GitHub API integration to retrieve repository metadata
- Repository filtering against quality criteria:
  - Minimum 50 GitHub stars
  - Repository size between 50,000 KB and 1,000,000 KB
  - Supported programming language
  - Valid default branch
  - Valid licence information

### 2. Repository Processing
- Automated repository cloning at scale
- Checkpointing, retry handling, and resume mechanisms to handle GitHub API rate limits, cloning failures, and network timeouts
- Source code extraction across multiple programming languages

### 3. Jupyter Notebook Handling
- Notebook language detection from repository metadata
- Extraction of executable code cells only
- Removal of notebook magic commands and shell commands
- Exclusion of markdown cells
- Conversion of notebooks into clean source code suitable for dataset generation

### 4. Quality Filtering and Deduplication (NVIDIA NeMo Curator)

**Quality Filters:**
- `NumberOfLinesOfCodeFilter`
- `AlphaFilter`
- `XMLHeaderFilter`
- `HTMLBoilerplateFilter`
- `TokenizerFertilityFilter`

**Deduplication:**
- Exact duplicate removal using hashing
- Fuzzy duplicate removal using character n-gram similarity

### 5. Dataset Generation
- Structured JSONL output format
- One record per source file
- Metadata-rich records for downstream filtering and research

---

## Dataset Schema

Each JSONL record contains the following fields:

```json
{
  "repo_name": "example/repository",
  "repo_description": "A sample Python project",
  "stars": 245,
  "file_count": 42,
  "repo_size_kb": 15200,
  "language": "Python",
  "license": "MIT",
  "file_name": "main.py",
  "text": "print('Hello, World!')"
}
```

---

## Engineering Challenges

- **GitHub API rate limits** — Handled via rate-limit detection, exponential backoff, and resume mechanisms
- **Repository cloning failures** — Managed through retry logic and checkpointing to allow interrupted runs to resume without reprocessing completed repositories
- **Network timeouts** — Handled with configurable timeout thresholds and automatic retries
- **Large-scale data processing** — Managed through parallel processing and memory-efficient streaming pipelines
- **CUDA and GPU environment configuration** — Resolved environment issues during NVIDIA NeMo Curator integration and experimentation

---

## Impact

- Improved dataset quality and diversity through structured quality filtering
- Reduced duplicate and low-quality code samples through exact and fuzzy deduplication
- Reduced memorisation risk in future LLM training datasets
- Created a scalable and reproducible foundation for future code LLM research and experimentation

---

## Tech Stack

- **Language:** Python
- **Dataset Curation:** NVIDIA NeMo Curator
- **Data Sources:** GH Archive, GitHub API
- **Output Format:** JSONL
- **Key Techniques:** Quality Filtering, Deduplication, Checkpointing, Retry Handling, Jupyter Notebook Processing

---

## Notes

This pipeline was built during an AI Engineer internship at the Home Team Science and Technology Agency (HTX), Singapore. The source code in this repository is a public representation of the pipeline architecture and design. Dataset outputs are not publicly available.
