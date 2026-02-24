"""Entry point for the Hackapizza multi-agent system.

Modes:
    Interactive: ./pizza_env/bin/python -m hackapizza_solution.main -q "question..."
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


def extract_ids_from_response(text: str) -> tuple[str, str | None]:
    """Extract numeric IDs from the LLM response, robust to various formats.
    Returns (ids_str, zero_cause). zero_cause is None when IDs were found, else a diagnostic string."""
    # Try to find "IDS: X,Y,Z" pattern first (from our tool)
    ids_match = re.search(r"IDS:\s*([\d,\s]+)", text)
    if ids_match:
        raw = ids_match.group(1)
        nums = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        if nums:
            return ",".join(str(n) for n in sorted(set(nums))), None
        return "0", "Formatter returned IDS: but no valid IDs in range 0-286"

    # Fallback: if the entire response is just numbers and commas
    clean = text.strip()
    if re.match(r"^[\d,\s]+$", clean):
        nums = [int(x.strip()) for x in clean.split(",") if x.strip().isdigit()]
        if nums:
            return ",".join(str(n) for n in sorted(set(nums))), None
        return "0", "Response is numeric but empty or invalid"

    # Fallback: extract all numbers from the text
    all_nums = re.findall(r"\b(\d{1,3})\b", text)
    valid = [int(n) for n in all_nums if 0 <= int(n) <= 286]
    if valid:
        return ",".join(str(n) for n in sorted(set(valid))), None
    if all_nums:
        invalid = [int(n) for n in all_nums if int(n) > 286 or int(n) < 0]
        return "0", f"Numbers found but outside valid ID range (0-286): {invalid[:5]}"

    # No numbers at all
    if not text or not text.strip():
        return "0", "Empty response from LLM"
    if "NOT FOUND" in text or "NON TROVATI" in text:
        return "0", "Dish names not found in mapping (NOT FOUND in response)"
    if "nessun" in text.lower() or "no dish" in text.lower() or "no chef" in text.lower():
        return "0", "Agents reported no matching dishes/chefs"
    return "0", "No numeric IDs in response - LLM may not have invoked formatter or returned unexpected format"


def prepare_data():
    """Run all data preparation steps (Phase 0)."""
    print("=" * 60)
    print("PHASE 0: Data preparation")
    print("=" * 60)

    print("\n--- Step 1: Parsing blogposts ---")
    from hackapizza_solution.data_preparation.parse_blogposts import run as parse_blogs
    parse_blogs()

    if not MENUS_JSON.exists():
        print("\n--- Step 2: Extracting menus from PDFs (LLM) ---")
        from hackapizza_solution.data_preparation.extract_menus import run as extract_menus
        extract_menus()
    else:
        print(f"\n--- Step 2: menus.json already present, skip ---")

    print("\n--- Step 3: Ingesting documents into Qdrant ---")
    from hackapizza_solution.data_preparation.ingest_rag import run as ingest_rag
    ingest_rag()

    print("\n" + "=" * 60)
    print("Data preparation complete!")
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
        print(f"Question: {question[:100]}{'...' if len(question) > 100 else ''}")
        print("-" * 60)

        start = time.time()
        zero_cause = None
        try:
            response = orchestrator.run(question)
            raw_answer = response.text
            ids_str, zero_cause = extract_ids_from_response(raw_answer)
        except Exception as e:
            raw_answer = f"ERROR: {e}"
            ids_str = "0"
            zero_cause = f"Exception during processing: {type(e).__name__}: {e}"
        elapsed = time.time() - start

        print(f"IDs: {ids_str}")
        print(f"Time: {elapsed:.1f}s")
        if ids_str == "0" and zero_cause:
            print(f"  >>> ZERO CAUSE: {zero_cause}")
            preview = raw_answer[:400] + ("..." if len(raw_answer) > 400 else "")
            print(f"  >>> Raw response preview: {preview}")

        kaggle_rows.append({"row_id": row_id, "result": ids_str})
        detailed_results.append({
            "row_id": row_id,
            "question": question,
            "ids": ids_str,
            "raw_response": raw_answer,
            "time_s": round(elapsed, 1),
            **({"zero_cause": zero_cause} if zero_cause else {}),
        })

    # Summary of zero-result cases for debugging
    zero_cases = [r for r in detailed_results if r.get("ids") == "0" and r.get("zero_cause")]
    if zero_cases:
        print(f"\n--- ZERO-RESULT SUMMARY ({len(zero_cases)} questions) ---")
        for r in zero_cases:
            print(f"  row_id={r['row_id']}: {r['zero_cause']}")

    # Write Kaggle submission CSV
    kaggle_csv = DATA_DIR / "submission.csv"
    with open(kaggle_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["row_id", "result"])
        writer.writeheader()
        writer.writerows(kaggle_rows)
    print(f"\nKaggle CSV saved to {kaggle_csv}")

    # Write detailed results JSON for debugging
    debug_json = DATA_DIR / "results_detailed.json"
    debug_json.write_text(
        json.dumps(detailed_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Detailed results saved to {debug_json}")

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
        print(f"Question: {args.question}\n")
        answer = run_single_question(args.question)
        ids, zero_cause = extract_ids_from_response(answer)
        print(f"\nRaw response:\n{answer}")
        print(f"\nExtracted IDs: {ids}")
        if ids == "0" and zero_cause:
            print(f"\n>>> ZERO CAUSE: {zero_cause}")
    elif args.batch:
        if not MENUS_JSON.exists():
            print("ERROR: menus.json not found. Run --prepare first")
            sys.exit(1)
        run_batch()
    else:
        print("Hackapizza Multi-Agent System")
        print("Type 'quit' to exit\n")

        from hackapizza_solution.agents.orchestrator import create_orchestrator
        orchestrator = create_orchestrator()

        while True:
            question = input("Question: ").strip()
            if question.lower() in ("quit", "exit", "q"):
                break
            if not question:
                continue
            try:
                response = orchestrator.run(question)
                ids, zero_cause = extract_ids_from_response(response.text)
                print(f"\nIDs: {ids}")
                if ids == "0" and zero_cause:
                    print(f">>> ZERO CAUSE: {zero_cause}")
                print(f"Raw: {response.text}\n")
            except Exception as e:
                print(f"\nERROR: {e}\n")


if __name__ == "__main__":
    main()
