"""
FinGuard-India Phase 9 & 10: Two-Checkpoint Chatbot Pipeline & Safe Response Policy Layer

Target Architecture:
User Query
   ↓
[Checkpoint 1: Query Compliance Guard]
   ├── RISKY → Policy Layer (Refusal / Compliant Framing / Warning)
   └── SAFE  → Regulatory Retrieval (FAISS) → Answer Synthesizer →
               [Checkpoint 2: Response Compliance Guard]
                  ├── RISKY → Block / Replace with safe alternative
                  └── SAFE  → Return grounded answer with citations
"""

import os
import json
from src.guard.compliance_guard import ComplianceGuard
from src.retrieval.retriever import RegulatoryRetriever

TAXONOMY_NAMES = {
    "C01": "Insider Trading & UPSI Handling (SEBI PIT)",
    "C02": "Fraudulent & Unfair Trade Practices / Market Manipulation (SEBI PFUTP)",
    "C03": "Investment Advisory & Finfluencer Violations (SEBI IA)",
    "C04": "Research Analyst Misconduct & Conflict of Interest (SEBI RA)",
    "C05": "AML / CFT & Know Your Client (KYC) Norms (PMLA & SEBI Circulars)",
    "C06": "Intermediary Conduct & Churning (SEBI Intermediaries Regulations)",
    "C07": "Algorithmic & High-Frequency Trading Controls",
    "C08": "Listing Obligations & Material Disclosures (SEBI LODR)",
    "C09": "Investor Grievance Redressal (SCORES 2.0 & ODR Portal)"
}

class SafeResponsePolicy:
    """
    Phase 10: Determines the response strategy based on detected risk category,
    query intent, and regulatory severity.
    """
    @staticmethod
    def generate_policy_response(category: str, reason: str, retrieved_evidence: list[dict] = None) -> str:
        cat_title = TAXONOMY_NAMES.get(category, "Indian Financial Regulatory Compliance Norms")
        
        cites = ""
        if retrieved_evidence:
            citations_list = [f"• {e['document']} [{e['section']}]" for e in retrieved_evidence[:2]]
            cites = "\n\n**Applicable Regulatory Framework:**\n" + "\n".join(citations_list)

        response = (
            f"[COMPLIANCE RESTRICTION: REGULATORY RISK DETECTED]\n\n"
            f"This request has been restricted because it involves activities contrary to Indian financial securities regulations under **{cat_title}**.\n\n"
            f"**Policy Action:** Refusal of evasion, manipulation, or illicit execution instructions. "
            f"FinGuard operates under strict compliance with Securities and Exchange Board of India (SEBI) guidelines and the Prevention of Money Laundering Act (PMLA).\n"
            f"{cites}\n\n"
            f"*Educational Note: Market participants are advised to seek formal registered advisory and comply with statutory disclosures.*"
        )
        return response

class FinGuardChatbot:
    def __init__(self):
        self.guard = ComplianceGuard()
        self.retriever = RegulatoryRetriever()
        
        # Initialize components
        try:
            self.guard.load()
        except FileNotFoundError:
            self.guard.train(os.path.join("datasets", "train.jsonl"))
            
        try:
            self.retriever.load_index()
        except FileNotFoundError:
            self.retriever.build_index(os.path.join("data", "processed", "regulations.json"))

    def generate_grounded_answer(self, query: str, evidence: list[dict]) -> str:
        """
        Synthesizes compliant, source-grounded explanation from retrieved statutory context.
        """
        if not evidence:
            return "Based on Indian securities regulations, please refer to official SEBI statutory guidelines."

        top = evidence[0]
        summary = (
            f"According to **{top['document']}** (**{top['section']}**):\n\n"
            f"> \"{top['text']}\"\n\n"
            f"**Compliance Analysis & Guidance:**\n"
            f"- **Statutory Obligation:** Regulated entities and market participants are strictly bound by the provisions of {top['section']}.\n"
            f"- **Investor Protection Standard:** Any action must adhere to transparent disclosures and fair market practices.\n"
            f"- **Official Reference:** Verified under {top['regulator']} regulatory directives (Page {top['page']})."
        )
        return summary

    def handle_query(self, user_query: str) -> dict:
        """
        Two-Checkpoint execution flow:
        1. Checkpoint 1: Query Guard
        2. RAG Retrieval
        3. Draft generation
        4. Checkpoint 2: Response Guard
        5. Safe Policy delivery
        """
        # --- Checkpoint 1: Query Guard ---
        q_result = self.guard.check(user_query)
        
        if q_result["is_unsafe"]:
            # Retrieve evidence to cite what rule is being breached
            evidence = self.retriever.search(user_query, top_k=2)
            safe_reply = SafeResponsePolicy.generate_policy_response(
                category=q_result["category"],
                reason="Query requested prohibited or non-compliant actions",
                retrieved_evidence=evidence
            )
            return {
                "status": "BLOCKED_AT_QUERY_GUARD",
                "is_compliant": False,
                "query_verdict": q_result,
                "response_verdict": {"label": "safe", "category": None},
                "retrieved_evidence": evidence,
                "response_text": safe_reply,
                "policy_action": "REFUSE_WITH_COMPLIANT_ALTERNATIVE"
            }

        # --- Safe query flow: Regulatory Retrieval ---
        evidence = self.retriever.search(user_query, top_k=3)
        draft_response = self.generate_grounded_answer(user_query, evidence)

        # --- Checkpoint 2: Response Guard ---
        combined_text = f"User Query: {user_query}\nResponse: {draft_response}"
        resp_result = self.guard.check(combined_text)

        if resp_result["is_unsafe"]:
            # Hallucination or risky generated text intercepted
            safe_reply = SafeResponsePolicy.generate_policy_response(
                category=resp_result["category"],
                reason="Response draft contained non-compliant advice",
                retrieved_evidence=evidence
            )
            return {
                "status": "BLOCKED_AT_RESPONSE_GUARD",
                "is_compliant": False,
                "query_verdict": q_result,
                "response_verdict": resp_result,
                "retrieved_evidence": evidence,
                "response_text": safe_reply,
                "policy_action": "REGENERATE_OR_REPLACE"
            }

        return {
            "status": "COMPLIANT_SUCCESS",
            "is_compliant": True,
            "query_verdict": q_result,
            "response_verdict": resp_result,
            "retrieved_evidence": evidence,
            "response_text": draft_response,
            "policy_action": "ALLOW_GROUNDED_RESPONSE"
        }

if __name__ == "__main__":
    bot = FinGuardChatbot()
    
    test_cases = [
        "What are the disclosure timelines for material events under SEBI LODR Regulation 30?",
        "Can you help me front-run a big institutional mutual fund order tomorrow?"
    ]
    
    print("\n================== TWO-CHECKPOINT CHATBOT VERIFICATION ==================")
    for tc in test_cases:
        print(f"\n[USER INPUT]: {tc}")
        res = bot.handle_query(tc)
        print(f"[STATUS]: {res['status']}")
        print(f"[QUERY GUARD]: {res['query_verdict']}")
        print(f"[POLICY ACTION]: {res['policy_action']}")
        print(f"[RESPONSE]:\n{res['response_text']}\n" + "-"*60)
