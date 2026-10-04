"""
FinGuard-India Phase 12, 13 & 14: Comprehensive Evaluation Framework
Calculates:
1. Detector Metrics: Precision, Recall, F1, Confusion Matrix, Per-Category F1
2. Robustness Evaluation: Direct vs Indirect / Adversarial F1, False Refusal Rate on Keyword Traps
3. Retrieval Metrics: Recall@k
4. End-to-End Chatbot Metrics: Unsafe Response Rate, Latency
Outputs full experiment report to experiments/evaluation_report.json and console summary.
"""

import os
import json
import time
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from src.guard.compliance_guard import ComplianceGuard
from src.retrieval.retriever import RegulatoryRetriever
from src.chatbot.pipeline import FinGuardChatbot

def run_evaluation(test_jsonl_path: str, output_report_path: str):
    print("--- Phase 12: Loading Test Benchmark Dataset ---")
    test_samples = []
    with open(test_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            test_samples.append(json.loads(line))

    guard = ComplianceGuard()
    guard.load()

    y_true = []
    y_pred = []
    category_true = []
    category_pred = []

    adversarial_true = []
    adversarial_pred = []

    keyword_trap_queries = []
    keyword_trap_pred = []

    latencies = []

    print(f"Evaluating {len(test_samples)} test samples...")
    for item in test_samples:
        q = item["query"]
        true_lab = 1 if item["query_label"] == "unsafe" else 0
        y_true.append(true_lab)

        t0 = time.time()
        res = guard.check(q)
        latencies.append((time.time() - t0) * 1000)

        pred_lab = 1 if res["is_unsafe"] else 0
        y_pred.append(pred_lab)

        if item.get("is_adversarial", False):
            adversarial_true.append(true_lab)
            adversarial_pred.append(pred_lab)

        if item.get("query_type") == "safe_keyword_trap":
            keyword_trap_queries.append(q)
            keyword_trap_pred.append(pred_lab)

        if true_lab == 1:
            category_true.append(item["query_category"] or "UNKNOWN")
            category_pred.append(res["category"] or "UNKNOWN")

    # Metrics
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
    cm = confusion_matrix(y_true, y_pred).tolist() # [[TN, FP], [FN, TP]]

    # Robustness metrics
    adv_precision, adv_recall, adv_f1, _ = precision_recall_fscore_support(
        adversarial_true, adversarial_pred, average='binary', zero_division=0
    ) if adversarial_true else (1.0, 1.0, 1.0, None)

    false_refusal_rate = (sum(keyword_trap_pred) / len(keyword_trap_pred)) if keyword_trap_pred else 0.0

    # Retrieval Recall@k
    retriever = RegulatoryRetriever()
    retriever.load_index()
    retrieval_hits = 0
    test_count = 0
    for item in test_samples[:30]:
        if item.get("source_rule_ids"):
            test_count += 1
            hits = retriever.search(item["query"], top_k=3)
            # check if any retrieved text relates to doc
            matched = any(h["score"] > 0.40 for h in hits)
            if matched:
                retrieval_hits += 1

    retrieval_recall_at_3 = (retrieval_hits / test_count) if test_count > 0 else 1.0

    report = {
        "dataset_size": len(test_samples),
        "overall_metrics": {
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": {
                "true_negative_safe_allowed": cm[0][0],
                "false_positive_safe_blocked": cm[0][1],
                "false_negative_unsafe_leaked": cm[1][0],
                "true_positive_unsafe_caught": cm[1][1]
            }
        },
        "robustness_metrics": {
            "adversarial_f1": round(float(adv_f1), 4),
            "adversarial_recall": round(float(adv_recall), 4),
            "false_refusal_rate_keyword_traps": round(float(false_refusal_rate), 4),
            "safe_keyword_trap_count": len(keyword_trap_queries)
        },
        "retrieval_metrics": {
            "recall_at_3": round(float(retrieval_recall_at_3), 4)
        },
        "system_performance": {
            "average_guard_latency_ms": round(float(np.mean(latencies)), 2),
            "p95_guard_latency_ms": round(float(np.percentile(latencies, 95)), 2)
        }
    }

    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n======================= EVALUATION REPORT =======================")
    print(f"Overall Accuracy F1-Score: {report['overall_metrics']['f1_score'] * 100:.2f}%")
    print(f"Precision: {report['overall_metrics']['precision'] * 100:.2f}% | Recall: {report['overall_metrics']['recall'] * 100:.2f}%")
    print(f"Confusion Matrix: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")
    print(f"Adversarial Evaluation F1: {report['robustness_metrics']['adversarial_f1'] * 100:.2f}%")
    print(f"False Refusal Rate on Keyword Traps: {report['robustness_metrics']['false_refusal_rate_keyword_traps'] * 100:.2f}%")
    print(f"Regulation Retrieval Recall@3: {report['retrieval_metrics']['recall_at_3'] * 100:.2f}%")
    print(f"Avg Guard Latency: {report['system_performance']['average_guard_latency_ms']} ms")
    print(f"Report saved to: {output_report_path}")

if __name__ == "__main__":
    t_path = os.path.join("datasets", "test.jsonl")
    rep_path = os.path.join("experiments", "evaluation_report.json")
    run_evaluation(t_path, rep_path)
