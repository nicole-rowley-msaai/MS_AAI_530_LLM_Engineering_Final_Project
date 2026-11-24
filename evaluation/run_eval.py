
"""Run FitCheck AI on the test set and save one row per suggested bullet.

Usage, from the project root:

    python -m evaluation.run_eval --prompt-version v2
    python -m evaluation.run_eval --prompt-version v1 --limit 3

Input:  a CSV with the columns pair_id, resume, job_posting
        (default: data/test_set/pairs.csv)
Output: evaluation/results/results_<prompt version>.csv

Each run calls the OpenAI API twice per pair, which costs money.
Use --limit for a small trial run first.
"""

import argparse
import csv
from pathlib import Path

from src.assistant import ASSISTANT_MODEL, analyze_resume
from src.judge import (
    JUDGE_MODEL,
    judge_suggestions,
    quote_in_resume,
    verdicts_by_index,
)
from src.prompts import DEFAULT_PROMPT_VERSION, PROMPTS


RESULTS_DIR = Path("evaluation/results")

COLUMNS = [
    "pair_id",
    "prompt_version",
    "assistant_model",
    "judge_model",
    "overall_fit",
    "bullet_index",
    "original_text",
    "suggested_text",
    "original_in_resume",
    "label",
    "evidence",
    "evidence_in_resume",
    "reason",
]


# Run the assistant and judge on one pair and return one row per bullet.
def evaluate_pair(pair: dict, prompt_version: str) -> list[dict]:
    resume = pair["resume"]

    result = analyze_resume(resume, pair["job_posting"], prompt_version)
    judge_result = judge_suggestions(resume, result.resume_suggestions)
    verdicts = verdicts_by_index(judge_result, len(result.resume_suggestions))

    rows = []

    for index, suggestion in enumerate(result.resume_suggestions):
        verdict = verdicts.get(index)

        rows.append({
            "pair_id": pair["pair_id"],
            "prompt_version": prompt_version,
            "assistant_model": ASSISTANT_MODEL,
            "judge_model": JUDGE_MODEL,
            "overall_fit": result.overall_fit,
            "bullet_index": index,
            "original_text": suggestion.original_text,
            "suggested_text": suggestion.suggested_text,
            "original_in_resume": quote_in_resume(
                suggestion.original_text, resume
            ),
            "label": verdict.label if verdict else "not_checked",
            "evidence": verdict.evidence if verdict else "",
            "evidence_in_resume": bool(
                verdict and quote_in_resume(verdict.evidence, resume)
            ),
            "reason": verdict.reason if verdict else "",
        })

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--prompt-version",
        default=DEFAULT_PROMPT_VERSION,
        choices=list(PROMPTS),
    )
    parser.add_argument("--pairs", default="data/test_set/pairs.csv")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only run the first N pairs",
    )
    args = parser.parse_args()

    with open(args.pairs, newline="", encoding="utf-8") as file:
        pairs = list(csv.DictReader(file))

    if args.limit is not None:
        pairs = pairs[:args.limit]

    rows = []
    failed = []

    for number, pair in enumerate(pairs, start=1):
        print(f"[{number}/{len(pairs)}] pair {pair['pair_id']}")

        # Record failures and continue, so one bad pair does not end the run.
        try:
            rows.extend(evaluate_pair(pair, args.prompt_version))
        except Exception as error:
            print(f"  failed: {error}")
            failed.append(pair["pair_id"])

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"results_{args.prompt_version}.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Print the headline numbers for this prompt version.
    total = len(rows)
    print(f"\nSaved {total} bullets from {len(pairs) - len(failed)} pairs "
          f"to {output_path}")

    if total:
        for label in ("supported", "exaggerated", "unsupported", "not_checked"):
            count = sum(row["label"] == label for row in rows)
            print(f"  {label:<12} {count:>4}  ({count / total:.0%})")

    if failed:
        print(f"Failed pairs: {', '.join(failed)}")


if __name__ == "__main__":
    main()
