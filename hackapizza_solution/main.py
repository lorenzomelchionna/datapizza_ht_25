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
from hackapizza_solution.config import (
    DOMANDE_CSV, MENUS_JSON, BLOGPOST_PCT_JSON, DATA_DIR,
    QDRANT_HOST, QDRANT_PORT,
    COLLECTION_CODICE, COLLECTION_MANUALE, COLLECTION_BLOG,
)

# Valid dish ID range (from dish_mapping.json)
VALID_ID_MIN, VALID_ID_MAX = 0, 286


def _check_qdrant_collections() -> list[str]:
    """Verify Qdrant is running and required collections exist. Returns list of missing collections."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        required = [COLLECTION_CODICE, COLLECTION_MANUALE, COLLECTION_BLOG]
        missing = [c for c in required if not client.collection_exists(c)]
        return missing
    except Exception as e:
        return [f"Qdrant unreachable: {e}"]


def extract_ids_from_response(text: str) -> tuple[str, str | None]:
    """Extract numeric IDs from the LLM response. Only trusts explicit ID patterns to avoid
    false positives (e.g. percentages, years, distances). Returns (ids_str, zero_cause)."""
    def _filter_valid_ids(nums: list[int]) -> list[int]:
        return sorted(set(n for n in nums if VALID_ID_MIN <= n <= VALID_ID_MAX))

    # Try to find "IDS: X,Y,Z" pattern first (from our formatter tool - explicit output)
    ids_match = re.search(r"IDS:\s*([\d,\s]+)", text, re.IGNORECASE)
    if ids_match:
        raw = ids_match.group(1)
        nums = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        valid = _filter_valid_ids(nums)
        if valid:
            return ",".join(str(n) for n in valid), None
        if nums:
            invalid = [n for n in nums if n < VALID_ID_MIN or n > VALID_ID_MAX]
            return "0", f"Formatter returned IDs outside valid range ({VALID_ID_MIN}-{VALID_ID_MAX}): {invalid[:5]}"
        return "0", "Formatter returned IDS: but no valid IDs"

    # Fallback: if the entire response is ONLY numbers and commas (orchestrator passthrough)
    clean = text.strip()
    if re.match(r"^[\d,\s]+$", clean):
        nums = [int(x.strip()) for x in clean.split(",") if x.strip().isdigit()]
        valid = _filter_valid_ids(nums)
        if valid:
            return ",".join(str(n) for n in valid), None
        if nums:
            invalid = [n for n in nums if n < VALID_ID_MIN or n > VALID_ID_MAX]
            return "0", f"Response contains numbers outside valid ID range ({VALID_ID_MIN}-{VALID_ID_MAX}): {invalid[:5]}"
        return "0", "Response is numeric but empty"

    # No fallback: do NOT extract numbers from free text (avoids false positives from
    # percentages, distances, years, counts, etc.)
    if not text or not text.strip():
        return "0", "Empty response from LLM"
    if "NOT FOUND" in text or "NON TROVATI" in text:
        return "0", "Dish names not found in mapping (NOT FOUND in response)"
    if "nessun" in text.lower() or "no dish" in text.lower() or "no chef" in text.lower():
        return "0", "Agents reported no matching dishes/chefs"
    return "0", "No explicit IDs in response - LLM may not have invoked formatter or returned unexpected format"


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
    # Pre-flight: verify Qdrant collections exist
    missing = _check_qdrant_collections()
    if missing:
        print("ERROR: Qdrant pre-flight check failed:")
        for m in missing:
            print(f"  - {m}")
        print("\nRun 'python -m hackapizza_solution.main --prepare' to create collections.")
        sys.exit(1)

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
        raw_answer = ""
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                response = orchestrator.run(question)
                raw_answer = response.text
                ids_str, zero_cause = extract_ids_from_response(raw_answer)
                break
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                # Retry on transient errors (connection refused, timeout, 5xx)
                is_transient = (
                    "connection refused" in err_str or "errno 61" in err_str
                    or "timeout" in err_str or "timed out" in err_str
                    or "503" in err_str or "502" in err_str or "504" in err_str
                )
                if is_transient and attempt < max_retries - 1:
                    wait = 5 * (attempt + 1)
                    print(f"  Retry {attempt + 1}/{max_retries - 1} after {wait}s...")
                    time.sleep(wait)
                else:
                    raw_answer = str(e)
                    ids_str = "0"
                    err_msg = str(e)
                    if "404" in err_msg and "doesn't exist" in err_msg.lower():
                        zero_cause = f"Qdrant collection missing: {err_msg[:150]}... Run --prepare first."
                    else:
                        zero_cause = f"Exception during processing: {type(e).__name__}: {e}"
                    break
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
