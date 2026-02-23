"""Entry point for the Hackapizza multi-agent system.

Modes:
    Interactive: ./pizza_env/bin/python -m hackapizza_solution.main -q "domanda..."
    Batch:       ./pizza_env/bin/python -m hackapizza_solution.main --batch
    Prepare:     ./pizza_env/bin/python -m hackapizza_solution.main --prepare
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hackapizza_solution.config import DOMANDE_CSV, MENUS_JSON, BLOGPOST_PCT_JSON, DATA_DIR


def extract_ids_from_response(text: str) -> str:
    """Extract numeric IDs from the LLM response, robust to various formats.
    Returns a comma-separated string of sorted unique IDs."""
    # Try to find "IDS: X,Y,Z" pattern first (from our tool)
    ids_match = re.search(r"IDS:\s*([\d,\s]+)", text)
    if ids_match:
        raw = ids_match.group(1)
        nums = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        if nums:
            return ",".join(str(n) for n in sorted(set(nums)))

    # Fallback: if the entire response is just numbers and commas
    clean = text.strip()
    if re.match(r"^[\d,\s]+$", clean):
        nums = [int(x.strip()) for x in clean.split(",") if x.strip().isdigit()]
        if nums:
            return ",".join(str(n) for n in sorted(set(nums)))

    # Fallback: extract all numbers from the text
    all_nums = re.findall(r"\b(\d{1,3})\b", text)
    # Filter to valid dish ID range (0-286)
    valid = [int(n) for n in all_nums if 0 <= int(n) <= 286]
    if valid:
        return ",".join(str(n) for n in sorted(set(valid)))

    return "0"


def prepare_data():
    """Run all data preparation steps (Phase 0)."""
    print("=" * 60)
    print("FASE 0: Preparazione dati")
    print("=" * 60)

    print("\n--- Step 1: Parsing blogposts ---")
    from hackapizza_solution.data_preparation.parse_blogposts import run as parse_blogs
    parse_blogs()

    if not MENUS_JSON.exists():
        print("\n--- Step 2: Extracting menus from PDFs (LLM) ---")
        from hackapizza_solution.data_preparation.extract_menus import run as extract_menus
        extract_menus()
    else:
        print(f"\n--- Step 2: menus.json gia presente, skip ---")

    print("\n--- Step 3: Ingesting documents into Qdrant ---")
    from hackapizza_solution.data_preparation.ingest_rag import run as ingest_rag
    ingest_rag()

    print("\n" + "=" * 60)
    print("Preparazione dati completata!")
    print("=" * 60)


def run_single_question(question: str) -> str:
    """Process a single question through the orchestrator."""
    from hackapizza_solution.agents.orchestrator import create_orchestrator

    orchestrator = create_orchestrator()
    response = orchestrator.run(question)
    return response.text


def run_batch():
    """Process all questions from domande.csv and produce Kaggle CSV."""
    from hackapizza_solution.agents.orchestrator import create_orchestrator

    orchestrator = create_orchestrator()

    with open(DOMANDE_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        questions = [row["domanda"] for row in reader]

    print(f"Processing {len(questions)} questions...\n")

    kaggle_rows = []
    detailed_results = []

    for i, question in enumerate(questions, 1):
        row_id = i
        print(f"\n{'='*60}")
        print(f"[{i}/{len(questions)}] row_id={row_id}")
        print(f"Domanda: {question[:100]}{'...' if len(question) > 100 else ''}")
        print("-" * 60)

        start = time.time()
        try:
            response = orchestrator.run(question)
            raw_answer = response.text
            ids_str = extract_ids_from_response(raw_answer)
        except Exception as e:
            raw_answer = f"ERRORE: {e}"
            ids_str = "0"
        elapsed = time.time() - start

        print(f"IDs: {ids_str}")
        print(f"Tempo: {elapsed:.1f}s")

        kaggle_rows.append({"row_id": row_id, "result": ids_str})
        detailed_results.append({
            "row_id": row_id,
            "domanda": question,
            "ids": ids_str,
            "raw_response": raw_answer,
            "tempo_s": round(elapsed, 1),
        })

    # Write Kaggle submission CSV
    kaggle_csv = DATA_DIR / "submission.csv"
    with open(kaggle_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["row_id", "result"])
        writer.writeheader()
        writer.writerows(kaggle_rows)
    print(f"\nKaggle CSV salvato in {kaggle_csv}")

    # Write detailed results JSON for debugging
    debug_json = DATA_DIR / "results_detailed.json"
    debug_json.write_text(
        json.dumps(detailed_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Risultati dettagliati salvati in {debug_json}")

    return kaggle_rows


def main():
    parser = argparse.ArgumentParser(description="Hackapizza Multi-Agent System")
    parser.add_argument(
        "-q", "--question", type=str, default=None,
        help="Process a single question interactively",
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Process all questions from domande.csv and produce Kaggle CSV",
    )
    parser.add_argument(
        "--prepare", action="store_true",
        help="Run data preparation (Phase 0): extract menus, parse blogs, ingest RAG",
    )
    args = parser.parse_args()

    if args.prepare:
        prepare_data()
    elif args.question:
        print(f"Domanda: {args.question}\n")
        answer = run_single_question(args.question)
        ids = extract_ids_from_response(answer)
        print(f"\nRisposta raw:\n{answer}")
        print(f"\nIDs estratti: {ids}")
    elif args.batch:
        if not MENUS_JSON.exists():
            print("ERRORE: menus.json non trovato. Esegui prima --prepare")
            sys.exit(1)
        run_batch()
    else:
        print("Hackapizza Multi-Agent System")
        print("Digita 'quit' per uscire\n")

        from hackapizza_solution.agents.orchestrator import create_orchestrator
        orchestrator = create_orchestrator()

        while True:
            question = input("Domanda: ").strip()
            if question.lower() in ("quit", "exit", "q"):
                break
            if not question:
                continue
            try:
                response = orchestrator.run(question)
                ids = extract_ids_from_response(response.text)
                print(f"\nIDs: {ids}")
                print(f"Raw: {response.text}\n")
            except Exception as e:
                print(f"\nERRORE: {e}\n")


if __name__ == "__main__":
    main()
