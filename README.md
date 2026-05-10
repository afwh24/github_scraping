# GitHub Scraping Pipeline

A large-scale GitHub repository scraping and dataset curation pipeline designed to collect permissively licensed source code repositories, extract file-level metadata, and prepare high-quality code datasets for AI and LLM training.

---

## Overview

This project replicates and extends concepts from datasets such as The Stack v2 by:

- Scraping repositories from GitHub
- Filtering repositories by quality and size
- Extracting source files and metadata
- Detecting programming languages and licenses
- Producing structured JSONL datasets
- Supporting large-scale distributed processing

The pipeline is designed for scalability, reproducibility, and automated monthly dataset collection.

---

## Features

### Repository Collection
- GH Archive event scraping
- GitHub API integration
- Repository filtering by:
  - Stars
  - Repository size
  - License
  - Language

### Repository Processing
- Automatic repository cloning
- Main branch detection
- Large repository handling
- Checkpointing and resume support

### File Extraction
- File-level metadata extraction
- Source code filtering
- Encoding detection
- Extension validation
- Non-code file removal

### Language Detection
- go-enry language classification
- Jupyter Notebook metadata parsing
- Notebook code cell extraction

### License Detection
- ScanCode Toolkit integration
- Permissive license filtering

### Dataset Generation
- JSONL output format
- Monthly dataset segmentation
- Metadata-rich records

---

## Dataset Schema

Each extracted file contains metadata similar to:

```json
{
  "repo_name": "example/repository",
  "file_name": "main.py",
  "language": "Python",
  "license": "MIT",
  "stars": 245,
  "size_kb": 12,
  "encoding": "utf-8",
  "text": "print('Hello World')"
}
