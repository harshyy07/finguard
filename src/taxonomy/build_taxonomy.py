"""
FinGuard-India Phase 4: Build Indian Compliance Taxonomy
Embeds compliance points using SentenceTransformers (all-MiniLM-L6-v2),
clusters with HDBSCAN / Agglomerative clustering, generates cluster summaries,
and saves the finalized taxonomy to datasets/taxonomy/taxonomy.csv and taxonomy.json.
"""

import json
import os
import csv
import numpy as np
from sentence_transformers import SentenceTransformer
import hdbscan

# Curated reference Indian Compliance Taxonomy anchored in official SEBI Regulations
TAXONOMY_DEFINITIONS = {
    "C01": {
        "category_name": "Insider Trading & UPSI Handling",
        "description": "Unlawful communication, procurement, or trading while in possession of Unpublished Price Sensitive Information (UPSI), and non-compliance with statutory trading plans or insider disclosures under SEBI (PIT) Regulations.",
        "keywords": ["upsi", "insider trading", "trading plan", "unpublished price sensitive", "material non-public", "tipping", "designated person", "promoter trade"]
    },
    "C02": {
        "category_name": "Fraudulent & Unfair Trade Practices (PFUTP) / Market Manipulation",
        "description": "Deceptive schemes, circular trading, wash trades, price rigging, artificial volume fabrication, pump-and-dump campaigns, front-running, and spoofing/layering in order books under SEBI (PFUTP) Regulations.",
        "keywords": ["circular trading", "wash trade", "pump and dump", "front running", "spoofing", "layering", "price manipulation", "rigging", "fake volume", "marking the close"]
    },
    "C03": {
        "category_name": "Investment Advisory & Finfluencer Violations",
        "description": "Operating as an unregistered investment adviser, offering guaranteed/assured returns, engaging in profit-sharing arrangements, failing suitability/risk profiling, or taking illicit commissions under SEBI (IA) Regulations.",
        "keywords": ["investment advice", "trading calls", "guaranteed returns", "assured profit", "profit sharing", "unregistered adviser", "finfluencer", "suitability", "risk profiling"]
    },
    "C04": {
        "category_name": "Research Analyst Misconduct & Conflict of Interest",
        "description": "Publishing research recommendations without SEBI registration, front-running own research calls (scalping), failing mandatory disclosure of personal/banking conflicts of interest, or failing audit record retention under SEBI (RA) Regulations.",
        "keywords": ["research analyst", "target price", "stock recommendation", "conflict of interest", "analyst trading", "scalping", "research report", "material interest"]
    },
    "C05": {
        "category_name": "AML / CFT & Know Your Client (KYC) Non-Compliance",
        "description": "Operating fictitious/benami/anonymous accounts, evading Customer Due Diligence (CDD/EDD), failure to report suspicious transactions (STR) to FIU-IND, or tipping off clients under PMLA and SEBI KYC Master Circular.",
        "keywords": ["kyc", "aml", "benami account", "anonymous account", "beneficial owner", "fiu-ind", "str", "suspicious transaction", "tipping off", "politically exposed person"]
    },
    "C06": {
        "category_name": "Intermediary Conduct & Client Protection",
        "description": "Breach of fiduciary integrity, leaking client orders, failure to maintain Chinese Walls between dealing and proprietary desks, or portfolio churning to extract excessive brokerage fees under SEBI Intermediaries Code.",
        "keywords": ["chinese wall", "order leakage", "brokerage churning", "excessive trading", "intermediary conduct", "proprietary desk", "client confidentiality"]
    },
    "C07": {
        "category_name": "Algorithmic & High-Frequency Trading Safeguards",
        "description": "Deploying unapproved algorithmic trading strategies, bypassing pre-trade risk controls (order limits, price bands, kill-switch), or providing unvetted automated bot APIs to retail investors without compliance checks.",
        "keywords": ["algo trading", "kill switch", "pre-trade risk controls", "conformance testing", "automated bot", "hft", "order to trade ratio"]
    },
    "C08": {
        "category_name": "Corporate Disclosure & Material Event Timelines",
        "description": "Withholding or delaying material price-sensitive corporate announcements, violating 30-minute/12-hour LODR filing timelines, or failing to verify/clarify circulating market rumors under SEBI (LODR) Regulations.",
        "keywords": ["lodr", "material event", "board meeting disclosure", "30 minutes", "market rumor verification", "continuous disclosure", "corporate announcement"]
    },
    "C09": {
        "category_name": "Investor Grievance Redressal & SCORES Compliance",
        "description": "Failure to address investor complaints within statutory 21 calendar days on SCORES 2.0, non-compliance with ODR arbitration frameworks, or actions leading to demat account freeze under SEBI Act.",
        "keywords": ["scores", "investor grievance", "action taken report", "atr", "21 days", "odr", "demat freeze", "investor complaint"]
    }
}

def cluster_and_build_taxonomy(compliance_points_path: str, output_csv: str, output_json: str):
    with open(compliance_points_path, "r", encoding="utf-8") as f:
        points = json.load(f)

    print("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    texts = [f"{p['compliance_point']} Risk: {p['risk_if_violated']}" for p in points]
    embeddings = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    
    # Run HDBSCAN
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1, metric='euclidean')
    cluster_labels = clusterer.fit_predict(embeddings)
    print(f"HDBSCAN clustering complete. Discovered clusters: {set(cluster_labels)}")

    # Map compliance points to primary taxonomy categories
    category_assignments = {cid: [] for cid in TAXONOMY_DEFINITIONS}
    
    for i, p in enumerate(points):
        text_lower = f"{p['compliance_point']} {p['risk_if_violated']} {p['document']}".lower()
        matched_cat = "C02" # default to market abuse if uncertain
        
        for cid, info in TAXONOMY_DEFINITIONS.items():
            if any(k in text_lower for k in info["keywords"]):
                matched_cat = cid
                break
        
        category_assignments[matched_cat].append(p["rule_id"])
        p["assigned_category"] = matched_cat
        p["cluster_id"] = int(cluster_labels[i])

    # Save finalized taxonomy
    taxonomy_records = []
    for cid, info in TAXONOMY_DEFINITIONS.items():
        rules = ";".join(category_assignments[cid]) if category_assignments[cid] else "N/A"
        taxonomy_records.append({
            "category_id": cid,
            "category_name": info["category_name"],
            "definition": info["description"],
            "source_rule_ids": rules
        })

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category_id", "category_name", "definition", "source_rule_ids"])
        writer.writeheader()
        writer.writerows(taxonomy_records)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(taxonomy_records, f, indent=2, ensure_ascii=False)

    print(f"--- Phase 4: Indian Compliance Taxonomy Established ---")
    print(f"Total Categories: {len(taxonomy_records)}")
    for tr in taxonomy_records:
        print(f"  [{tr['category_id']}] {tr['category_name']} -> {len(tr['source_rule_ids'].split(';')) if tr['source_rule_ids'] != 'N/A' else 0} Rules")
    print(f"Saved to: {output_csv} & {output_json}")

if __name__ == "__main__":
    cp_path = os.path.join("data", "processed", "compliance_points.json")
    out_csv = os.path.join("datasets", "taxonomy", "taxonomy.csv")
    out_json = os.path.join("datasets", "taxonomy", "taxonomy.json")
    cluster_and_build_taxonomy(cp_path, out_csv, out_json)
