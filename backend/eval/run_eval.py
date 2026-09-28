"""
Measures retrieval quality against the hand-labeled eval set.

Recall@k: for what fraction of questions did at least one correct
function appear in the top-k retrieved results? This is the headline
number to put in your README/resume — e.g. "Recall@5: 0.83".

MRR (Mean Reciprocal Rank): rewards ranking the correct answer HIGHER,
not just anywhere in the top-k. A correct answer at position 1 scores
1.0; at position 3 scores 0.33; missing entirely scores 0.

Run with (from inside backend/, with the server already running via
`uvicorn app.main:app --reload` in another terminal):

    python eval/run_eval.py                       # uses the default (sample repo) eval set
    python eval/run_eval.py eval/requests_eval_set.json   # uses a specific eval set
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.retriever import retrieve

DEFAULT_EVAL_SET_PATH = os.path.join(os.path.dirname(__file__), "retrieval_eval_set.json")
TOP_K = 5


def run_eval(eval_set_path: str = DEFAULT_EVAL_SET_PATH):
    with open(eval_set_path) as f:
        eval_set = json.load(f)

    recall_hits = 0
    reciprocal_ranks = []
    per_question_results = []

    for item in eval_set:
        question = item["question"]
        correct_units = set(item["correct_units"])

        results = retrieve(question, top_k=TOP_K)
        retrieved_units = [r["unit_name"] for r in results]

        # Recall@k: did ANY correct unit show up anywhere in top-k?
        hit = any(u in correct_units for u in retrieved_units)
        if hit:
            recall_hits += 1

        # MRR: 1 / rank of the FIRST correct unit found (0 if none found)
        rank = None
        for i, u in enumerate(retrieved_units, start=1):
            if u in correct_units:
                rank = i
                break
        reciprocal_rank = (1 / rank) if rank else 0
        reciprocal_ranks.append(reciprocal_rank)

        per_question_results.append({
            "question": question,
            "expected": list(correct_units),
            "retrieved": retrieved_units,
            "hit": hit,
            "rank_of_first_correct": rank,
        })

    recall_at_k = recall_hits / len(eval_set)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    print(f"\n{'='*50}")
    print(f"RETRIEVAL EVALUATION RESULTS  (top_k={TOP_K})")
    print(f"{'='*50}")
    for r in per_question_results:
        status = "HIT " if r["hit"] else "MISS"
        print(f"[{status}] rank={r['rank_of_first_correct']}  \"{r['question']}\"")
        print(f"         expected: {r['expected']}")
        print(f"         got:      {r['retrieved']}")
    print(f"{'='*50}")
    print(f"Recall@{TOP_K}: {recall_at_k:.2f}  ({recall_hits}/{len(eval_set)} questions)")
    print(f"MRR:       {mrr:.2f}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EVAL_SET_PATH
    run_eval(path)
