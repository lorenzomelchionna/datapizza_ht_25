# Hackapizza Solution Structure

Detailed documentation of the multi-agent architecture for answering the 100 hackathon questions about galactic restaurant menus.

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Execution Flow](#execution-flow)
4. [Configuration](#configuration)
5. [Phase 0: Data Preparation](#phase-0-data-preparation)
6. [Agents and Tools](#agents-and-tools)
7. [Question Classification](#question-classification)
8. [Output and Kaggle Format](#output-and-kaggle-format)

---

## Overview

The system is a **multi-agent orchestrator** that:

1. **Classifies** each question into one or more categories (A–L)
2. **Delegates** to specialized agents in the correct sequence
3. **Collects** intermediate results and passes them as context
4. **Formats** the final output as numeric dish IDs (Kaggle format)

Each agent has access to specific **tools** (menu search, RAG, distances, licenses, etc.) and communicates with others through the orchestrator.

---

## Directory Structure

```
hackapizza_solution/
├── main.py                 # Entry point: interactive, batch, prepare
├── config.py               # API keys, models, paths, Qdrant collections
├── STRUTTURA_SOLUZIONE.md  # Italian version of this documentation
│
├── data_preparation/       # Phase 0: data extraction and ingestion
│   ├── parse_blogposts.py  # Extracts ingredient % from 2 HTML blogposts
│   ├── extract_menus.py    # LLM extracts menus.json from 34 PDFs
│   └── ingest_rag.py       # Ingest Codice + Manuale + Blog into Qdrant
│
├── agents/                 # Specialized agents
│   ├── orchestrator.py     # Classifies and delegates to other agents
│   ├── menu_search.py      # Search dishes by ingredient/technique/location
│   ├── manual_expert.py    # Technique categories from Manuale (RAG)
│   ├── license_checker.py  # Verify chef licenses and technique requirements
│   ├── distance_calculator.py  # Distances between planets
│   ├── order_expert.py     # Professional orders (Codice + Manuale)
│   ├── compliance_checker.py   # Codice Galattico limit compliance
│   └── formatter.py        # Converts dish names → numeric IDs
│
├── tools/                  # Tools used by agents
│   ├── classifier_tool.py  # Wrapper for question_classifier
│   ├── menu_tools.py       # Search/filter on menus.json
│   ├── output_tools.py     # map_dishes_to_ids (dish_mapping.json)
│   ├── license_tools.py    # Chefs with license, technique requirements
│   ├── distance_tools.py   # Distances from Distanze.csv
│   ├── compliance_tools.py # Ingredient % (blogpost), substance limits
│   └── rag_tools.py        # RAG queries on Codice, Manuale, Blog
│
├── prompts/                # System prompt for each agent
│   ├── orchestrator.py
│   ├── menu_search.py
│   ├── manual_expert.py
│   ├── license_checker.py
│   ├── distance_calculator.py
│   ├── order_expert.py
│   ├── compliance_checker.py
│   └── formatter.py
│
└── data/                   # Generated output (created by --prepare / --batch)
    ├── menus.json          # Menus extracted from PDFs (34 restaurants)
    ├── blogpost_percentages.json  # Ingredient % from blogposts
    ├── submission.csv      # Kaggle output (row_id, result)
    └── results_detailed.json  # Detailed results for debugging
```

**Files outside the solution** (in project root):

- `question_classifier.py` — Hybrid classifier (rules + embedding) for categories A–L
- `hackapizza_dataset/` — Dataset: domande.csv, Menu/, Codice Galattico/, Misc/, Blogpost/

---

## Execution Flow

### Available Commands

| Command | Description |
|---------|-------------|
| `python -m hackapizza_solution.main` | Interactive mode (question loop) |
| `python -m hackapizza_solution.main -q "question..."` | Single question |
| `python -m hackapizza_solution.main --batch` | Process all 100 questions → submission.csv |
| `python -m hackapizza_solution.main --prepare` | Phase 0: extract menus, blog, ingest RAG |

### Pipeline per Question

```
User → main.py → Orchestrator
                        │
                        ├─ classify_question(question)  → categories A–L
                        │
                        ├─ [based on category] delegates to:
                        │     • menu_search
                        │     • manual_expert
                        │     • license_checker
                        │     • distance_calculator
                        │     • order_expert
                        │     • compliance_checker
                        │
                        └─ formatter (always last)
                              └─ map_dishes_to_ids(names) → "IDS: 23,45,67"
                        │
                        └─ extract_ids_from_response() → "23,45,67"
```

The orchestrator uses `can_call()` to delegate to agents; each agent can use its own tools and return structured text to the caller.

---

## Configuration

**File:** `config.py`

### Environment Variables (.env)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | LLM for all agents |
| `COHERE_API_KEY` | Embeddings for RAG (Qdrant) |
| `COHERE_ENDPOINT` | Cohere API URL (default: https://api.cohere.com) |
| `QDRANT_HOST` | Qdrant host (default: localhost) |
| `QDRANT_PORT` | Qdrant port (default: 6333) |

### Models

- `MODEL_FAST` (gpt-5-mini): menu_search, manual_expert, license, distance, formatter
- `MODEL_STRONG` (gpt-5): order_expert, compliance_checker (more complex questions)

### Main Paths

| Path | Description |
|------|-------------|
| `DATASET_DIR` | hackapizza_dataset/ |
| `DATA_DIR` | hackapizza_solution/data/ |
| `MENU_DIR` | Menu PDFs (34 files) |
| `MENUS_JSON` | Extracted menus (output of extract_menus) |
| `BLOGPOST_PCT_JSON` | Ingredient % (output of parse_blogposts) |
| `DOMANDE_CSV` | 100 questions |
| `DISTANZE_CSV` | Planet distance matrix |
| `DISH_MAPPING_JSON` | Dish name → numeric ID mapping |

### Qdrant Collections

- `codice_galattico` — Codice Galattico (PDF)
- `manuale_cucina` — Manuale di Cucina (PDF)
- `blogposts` — 2 HTML blogposts

---

## Phase 0: Data Preparation

Run with `--prepare`. Step order:

### 1. parse_blogposts

- **Input:** `hackapizza_dataset/Blogpost/*.html`
- **Output:** `data/blogpost_percentages.json`
- **Content:** Regulated ingredient percentages for reviewed dishes (e.g. "Carne di Drago": 8% in "Il Risveglio del Drago Celeste")
- **Use:** Compliance checker (Cat. K) to verify Codice Galattico limits

### 2. extract_menus

- **Input:** 34 PDFs in `Menu/`
- **Output:** `data/menus.json`
- **Content:** Per restaurant: name, planet, chef (name + licenses), dish list (name, ingredients, techniques)
- **Method:** pypdfium2 for text extraction + GPT with structured output (Pydantic)
- **Skip:** If `menus.json` already exists, step is skipped

### 3. ingest_rag

- **Input:** Codice Galattico PDF, Manuale di Cucina PDF, HTML blogposts
- **Output:** 3 Qdrant collections
- **Pipeline:** DoclingParser → RecursiveSplitter (2000 char, overlap 100) → CohereEmbedder → QdrantVectorstore
- **Requirements:** Qdrant running, Cohere API for embeddings

---

## Agents and Tools

### Orchestrator

- **Role:** Entry point; classifies and coordinates
- **Tool:** `classify_question`
- **Delegates to:** menu_search, manual_expert, license_checker, distance_calculator, order_expert, compliance_checker, formatter
- **Prompt:** Flows for categories A–L, agent sequence, formatter instructions

### Menu Search

- **Role:** Search and filter dishes from menus.json
- **Tools:**  
  - `search_dishes_by_ingredient`  
  - `search_dishes_by_technique`  
  - `filter_dishes_by_restaurant`  
  - `filter_dishes_by_planet`  
  - `get_chef_info`  
  - `get_all_dishes_with_details`

### Manual Expert

- **Role:** Answers on technique categories (taglio, surgelamento, etc.) from the Manuale
- **Tool:** `query_manuale_cucina` (RAG on `manuale_cucina` collection)

### License Checker

- **Role:** Verify chef licenses and technique requirements
- **Tools:** `get_chefs_with_license`, `get_required_licenses_for_technique`, `get_chef_info`
- **Note:** Technique requirements are in Codice/Manuale; the tool directs to RAG

### Distance Calculator

- **Role:** Calculate distances between planets
- **Tools:** `get_planets_within_radius`, `get_distance`
- **Data:** `Distanze.csv` (10×10 planet matrix)

### Order Expert

- **Role:** Expert on the 3 professional orders and their rules
- **Tools:** `query_codice_galattico`, `query_manuale_cucina`
- **Model:** MODEL_STRONG (more complex questions)

### Compliance Checker

- **Role:** Verify dish compliance with Codice Galattico limits
- **Tools:** `get_ingredient_percentages`, `get_substance_limits`, `query_codice_galattico`
- **Model:** MODEL_STRONG
- **Data:** blogpost_percentages.json for ingredient %; Codice for limits

### Formatter

- **Role:** Convert dish names to numeric IDs
- **Tool:** `map_dishes_to_ids` (uses dish_mapping.json)
- **Output:** `"IDS: 23,45,67"` (format parseable by extract_ids_from_response)

---

## Question Classification

**File:** `question_classifier.py` (project root)

**Categories (A–L):**

| Code | Name | Description | Data Sources |
|------|------|-------------|--------------|
| A | Ingredient filter | Dishes containing ingredient X | Menu, dish_mapping |
| B | Technique filter | Dishes prepared with technique Y | Menu, dish_mapping |
| C | AND combination | Dishes with A and B | Menu |
| D | NOT exclusion | Dishes without X | Menu |
| E | At least N from list | At least N among A,B,C | Menu |
| F | Restaurant/planet filter | By location | Menu |
| G | Chef license filter | Chefs with license X | Menu, Codice |
| H | Manuale categories | Techniques by category | Manuale (RAG) |
| I | Distance filter | Planets within N light-years | Distanze.csv, Menu |
| J | Order filter | Professional order | Codice, Manuale |
| K | Limit compliance | Ingredient % within limits | Blogpost, Codice |
| L | License compliance | Licenses for technique | Menu, Codice |

Questions can be **composite** (2+ categories). The orchestrator calls agents in the sequence specified in the prompt.

---

## Output and Kaggle Format

### submission.csv

- **Path:** `hackapizza_solution/data/submission.csv`
- **Format:** CSV with columns `row_id`, `result`
- **row_id:** 1–101 (row index in domande.csv)
- **result:** Comma-separated numeric IDs (e.g. `23,45,67`). If no dish: `0`

### results_detailed.json

- **Path:** `hackapizza_solution/data/results_detailed.json`
- **Content:** Per question: row_id, question, ids, raw_response, time_s
- **Use:** Debug and response analysis

### ID Extraction from LLM Response

`extract_ids_from_response()` in main.py:

1. Look for pattern `IDS: X,Y,Z`
2. Fallback: response is only numbers and commas
3. Fallback: extract all numbers 0–286 (valid ID range)
4. Default: `"0"` if no valid ID

---

## Main Dependencies

From `requirements.txt`:

- **datapizza-ai** — Agent framework, tools, RAG, pipeline
- **docling** — PDF parsing
- **qdrant-client** — Vector store
- **pydantic** — Structured models (extract_menus)
- **python-dotenv** — Environment variables

---

## Operational Notes

1. **First run:** Execute `--prepare` to generate menus.json, blogpost_percentages.json and populate Qdrant.
2. **Qdrant:** Must be running before `--prepare` and any RAG query.
3. **Batch:** `--batch` processes questions sequentially (1→101); the CSV is written only at the end.
4. **Estimated time:** ~2–5 min per question in batch; total ~3–8 hours for 100 questions.
