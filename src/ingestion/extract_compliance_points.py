"""
FinGuard-India Phase 3: Extract Compliance Points
Converts extracted statutory clauses into concise compliance obligations:
- What an entity/individual must do (OBLIGATION_MUST)
- What an entity/individual must not do (OBLIGATION_MUST_NOT)
- What must be disclosed (OBLIGATION_DISCLOSE)
Outputs data/processed/compliance_points.json
"""

import json
import os
import re

COMPLIANCE_RULES_MAP = [
    # PIT
    {
        "doc_match": "pit",
        "section_match": "3(1)",
        "rule_id": "SEBI_PIT_001",
        "compliance_point": "Insiders must not communicate or disclose Unpublished Price Sensitive Information (UPSI) to anyone except for legitimate business purposes or legal duties.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Illegal tipping of material non-public information leading to insider trading offenses."
    },
    {
        "doc_match": "pit",
        "section_match": "3(2)",
        "rule_id": "SEBI_PIT_002",
        "compliance_point": "No person shall solicit or procure Unpublished Price Sensitive Information (UPSI) from company insiders.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Procurement of illegal insider tips and unlawful trading advantages."
    },
    {
        "doc_match": "pit",
        "section_match": "4(1)",
        "rule_id": "SEBI_PIT_003",
        "compliance_point": "Insiders in possession of unpublished price sensitive information must not trade or execute transactions in company securities.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Direct insider trading liability, disgorgement of profits, criminal/civil penalties under SEBI Act."
    },
    {
        "doc_match": "pit",
        "section_match": "5(1)",
        "rule_id": "SEBI_PIT_004",
        "compliance_point": "Designated insiders must submit pre-approved trading plans to the compliance officer with a mandatory minimum six-month cooling-off period prior to execution.",
        "obligation_type": "MUST",
        "risk_if_violated": "Circumvention of insider trading safeguards through impromptu trades."
    },
    {
        "doc_match": "pit",
        "section_match": "7(2)",
        "rule_id": "SEBI_PIT_005",
        "compliance_point": "Promoters, directors, and designated persons must publicly disclose trades exceeding Rs. 10 Lakhs within two trading days.",
        "obligation_type": "DISCLOSE",
        "risk_if_violated": "Non-transparency of promoter/insider transactions impacting investor parity."
    },

    # PFUTP
    {
        "doc_match": "pfutp",
        "section_match": "3",
        "rule_id": "SEBI_PFUTP_001",
        "compliance_point": "Market participants must not use deceptive schemes, artifices, or fraudulent devices when buying or selling securities.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Securities fraud, market deception, and systemic risk."
    },
    {
        "doc_match": "pfutp",
        "section_match": "4(1)",
        "rule_id": "SEBI_PFUTP_002",
        "compliance_point": "Traders and entities must not create false or misleading appearance of active trading or artificial market liquidity.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Artificial volume fabrication misleading retail and institutional investors."
    },
    {
        "doc_match": "pfutp",
        "section_match": "4(2)(a)",
        "rule_id": "SEBI_PFUTP_003",
        "compliance_point": "Entities must not engage in circular trading, synchronized trades, or transactions lacking change in beneficial ownership.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Price rigging, volume manipulation, and fake pricing."
    },
    {
        "doc_match": "pfutp",
        "section_match": "4(2)(k)",
        "rule_id": "SEBI_PFUTP_004",
        "compliance_point": "Persons must not spread false rumors or tips via social media, Telegram, WhatsApp, or media to manipulate stock prices (Pump and Dump).",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Pump and dump schemes causing retail investor losses."
    },
    {
        "doc_match": "pfutp",
        "section_match": "4(2)(q)",
        "rule_id": "SEBI_PFUTP_005",
        "compliance_point": "Intermediaries and employees must not execute front-running trades ahead of substantial client or institutional orders.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Breach of fiduciary duty, theft of order flow value, front-running prosecution."
    },

    # Investment Advisers
    {
        "doc_match": "investment_advisers",
        "section_match": "3(1)",
        "rule_id": "SEBI_IA_001",
        "compliance_point": "Individuals and entities providing paid investment advice or trading calls must be registered with SEBI as an Investment Adviser.",
        "obligation_type": "MUST",
        "risk_if_violated": "Unregistered advisory activities, illegal 'finfluencer' operations, regulatory bans."
    },
    {
        "doc_match": "investment_advisers",
        "section_match": "15(1)",
        "rule_id": "SEBI_IA_002",
        "compliance_point": "Investment advisers must act in a strict fiduciary capacity and prioritize client financial interests.",
        "obligation_type": "MUST",
        "risk_if_violated": "Self-dealing and exploitation of investor trust."
    },
    {
        "doc_match": "investment_advisers",
        "section_match": "16(1)",
        "rule_id": "SEBI_IA_003",
        "compliance_point": "Investment advisers must perform mandatory risk profiling and verify suitability before recommending any securities or strategies.",
        "obligation_type": "MUST",
        "risk_if_violated": "Mis-selling high-risk speculative derivative products to unsuitable conservative investors."
    },
    {
        "doc_match": "investment_advisers",
        "section_match": "17(1)",
        "rule_id": "SEBI_IA_004",
        "compliance_point": "Advisers must not promise or guarantee fixed returns or enter profit-sharing percentage arrangements.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Fraudulent return promises, high-risk churn, and Ponzi-like structures."
    },
    {
        "doc_match": "investment_advisers",
        "section_match": "22",
        "rule_id": "SEBI_IA_005",
        "compliance_point": "Investment advisers must segregate advice from execution and must not accept distributor commissions from product providers.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Biased product distribution dressed as independent fee-only advisory."
    },

    # Research Analysts
    {
        "doc_match": "research_analysts",
        "section_match": "3",
        "rule_id": "SEBI_RA_001",
        "compliance_point": "Persons issuing stock recommendations or price targets to the public must hold valid SEBI Research Analyst registration.",
        "obligation_type": "MUST",
        "risk_if_violated": "Unlicensed market manipulation disguised as financial analysis."
    },
    {
        "doc_match": "research_analysts",
        "section_match": "16",
        "rule_id": "SEBI_RA_002",
        "compliance_point": "Research analysts must not trade in recommended securities within 30 days prior and 5 days after issuing a research report.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Trading ahead of recommendations (scalping / conflict of interest)."
    },
    {
        "doc_match": "research_analysts",
        "section_match": "19",
        "rule_id": "SEBI_RA_003",
        "compliance_point": "Research analysts must publicly disclose personal stock ownership, family holdings, and investment banking fees received from covered companies.",
        "obligation_type": "DISCLOSE",
        "risk_if_violated": "Undisclosed conflict of interest swaying investor decisions."
    },
    {
        "doc_match": "research_analysts",
        "section_match": "24",
        "rule_id": "SEBI_RA_004",
        "compliance_point": "Research entities must preserve all research models, rating basis, and documentation for at least five years.",
        "obligation_type": "MUST",
        "risk_if_violated": "Inability to substantiate analytical grounds during SEBI audit."
    },

    # KYC & AML
    {
        "doc_match": "kyc",
        "section_match": "2.1",
        "rule_id": "SEBI_KYC_001",
        "compliance_point": "Intermediaries must obtain and verify officially valid documents (PAN, Aadhaar) and verify the Beneficial Owner before onboarding clients.",
        "obligation_type": "MUST",
        "risk_if_violated": "Illegal market entry by benami or sanctioned entities."
    },
    {
        "doc_match": "kyc",
        "section_match": "3.4",
        "rule_id": "SEBI_KYC_002",
        "compliance_point": "Intermediaries must never maintain anonymous accounts, benami holdings, or fictitious-name client accounts.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Money laundering, terror financing, and hidden ownership networks."
    },
    {
        "doc_match": "kyc",
        "section_match": "5.2",
        "rule_id": "SEBI_KYC_003",
        "compliance_point": "Intermediaries must execute Enhanced Due Diligence (EDD) on Politically Exposed Persons (PEPs) and high-risk accounts.",
        "obligation_type": "MUST",
        "risk_if_violated": "Regulatory penalties under PMLA (Prevention of Money Laundering Act)."
    },
    {
        "doc_match": "kyc",
        "section_match": "7.1",
        "rule_id": "SEBI_KYC_004",
        "compliance_point": "Suspicious transactions must be reported to FIU-IND within 7 days; tipping off clients regarding STR filings is prohibited.",
        "obligation_type": "DISCLOSE",
        "risk_if_violated": "Failure to report AML violations and criminal breach under PMLA."
    },

    # Intermediaries
    {
        "doc_match": "intermediaries",
        "section_match": "Clause 1",
        "rule_id": "SEBI_INT_001",
        "compliance_point": "Intermediaries must exercise high integrity, diligence, and fair dealings toward all investors.",
        "obligation_type": "MUST",
        "risk_if_violated": "Breach of market code of conduct and suspension of intermediary license."
    },
    {
        "doc_match": "intermediaries",
        "section_match": "Clause 3",
        "rule_id": "SEBI_INT_002",
        "compliance_point": "Intermediaries must enforce physical and electronic information barriers (Chinese Walls) between proprietary and client dealing operations.",
        "obligation_type": "MUST",
        "risk_if_violated": "Information leakage and unauthorized cross-desk trading exploitation."
    },
    {
        "doc_match": "intermediaries",
        "section_match": "Clause 6",
        "rule_id": "SEBI_INT_003",
        "compliance_point": "Intermediaries must protect client transaction data and order books from unauthorized third-party disclosure.",
        "obligation_type": "MUST",
        "risk_if_violated": "Unauthorized client data leakage and trade privacy compromise."
    },
    {
        "doc_match": "intermediaries",
        "section_match": "Clause 9",
        "rule_id": "SEBI_INT_004",
        "compliance_point": "Brokers and intermediaries must not churn client portfolios or induce excessive trading to multiply brokerage commissions.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Investor wealth erosion via predatory churning."
    },

    # Surveillance
    {
        "doc_match": "surveillance",
        "section_match": "Paragraph 3",
        "rule_id": "SEBI_SURV_001",
        "compliance_point": "Market participants must not engage in spoofing or layering (placing non-genuine orders to mislead the order book followed by cancellation).",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Order-book manipulation, false depth creation, algorithmic abuse."
    },
    {
        "doc_match": "surveillance",
        "section_match": "Paragraph 6",
        "rule_id": "SEBI_SURV_002",
        "compliance_point": "Executing wash sales or self-trades without change of beneficial ownership is strictly prohibited.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Fabricated trade volumes and distorted price discovery."
    },
    {
        "doc_match": "surveillance",
        "section_match": "Paragraph 1",
        "rule_id": "SEBI_SURV_003",
        "compliance_point": "Participants must not execute trades at the market close intended solely to manipulate final benchmark settlement prices.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Marking the close and index settlement manipulation."
    },

    # Algo Trading
    {
        "doc_match": "algo_trading",
        "section_match": "1.2",
        "rule_id": "SEBI_ALGO_001",
        "compliance_point": "Brokers providing algorithmic trading must enforce automated pre-trade risk controls (price bands, quantity caps, and kill-switches).",
        "obligation_type": "MUST",
        "risk_if_violated": "Flash crashes, uncontained rogue algo loops, and exchange disruption."
    },
    {
        "doc_match": "algo_trading",
        "section_match": "2.1",
        "rule_id": "SEBI_ALGO_002",
        "compliance_point": "Every automated trading strategy must complete exchange conformance testing and obtain formal exchange approval prior to live execution.",
        "obligation_type": "MUST",
        "risk_if_violated": "Unapproved algo deployment and systemic exchange risk."
    },
    {
        "doc_match": "algo_trading",
        "section_match": "3.4",
        "rule_id": "SEBI_ALGO_003",
        "compliance_point": "Brokers must not grant unrestricted API access to unvetted third-party bot providers promising guaranteed retail returns.",
        "obligation_type": "MUST_NOT",
        "risk_if_violated": "Facilitation of illegal automated trading rackets."
    },

    # LODR Disclosures
    {
        "doc_match": "lodr",
        "section_match": "30(1)",
        "rule_id": "SEBI_LODR_001",
        "compliance_point": "Listed companies must disclose all material price-sensitive corporate events (mergers, defaults, board decisions) to stock exchanges.",
        "obligation_type": "DISCLOSE",
        "risk_if_violated": "Information asymmetry and selective disclosure offenses."
    },
    {
        "doc_match": "lodr",
        "section_match": "30(6)",
        "rule_id": "SEBI_LODR_002",
        "compliance_point": "Material board meeting decisions must be submitted within 30 minutes of board closure; internal events within 12 hours.",
        "obligation_type": "DISCLOSE",
        "risk_if_violated": "Delayed price-sensitive disclosures facilitating market leaks."
    },
    {
        "doc_match": "lodr",
        "section_match": "30(11)",
        "rule_id": "SEBI_LODR_003",
        "compliance_point": "Top listed entities must formally confirm, deny, or clarify market rumors within 24 hours of widespread publication.",
        "obligation_type": "DISCLOSE",
        "risk_if_violated": "Unverified speculation distorting market pricing."
    },

    # SCORES & Grievances
    {
        "doc_match": "scores",
        "section_match": "1.3",
        "rule_id": "SEBI_GRIEV_001",
        "compliance_point": "Intermediaries and listed companies must register on SCORES 2.0 and resolve investor grievances within 21 calendar days.",
        "obligation_type": "MUST",
        "risk_if_violated": "Investor grievance neglect, regulatory show-cause notice."
    },
    {
        "doc_match": "scores",
        "section_match": "2.4",
        "rule_id": "SEBI_GRIEV_002",
        "compliance_point": "Entities failing to resolve investor complaints within 21 days face demat freezing and monetary penalties under Section 15C.",
        "obligation_type": "MUST",
        "risk_if_violated": "Demat account freeze and daily regulatory fines."
    },
    {
        "doc_match": "scores",
        "section_match": "4.1",
        "rule_id": "SEBI_GRIEV_003",
        "compliance_point": "Unresolved investor complaints must be seamlessly escalated to Online Dispute Resolution (ODR) conciliation and arbitration.",
        "obligation_type": "MUST",
        "risk_if_violated": "Denial of fair redressal mechanisms to aggrieved retail investors."
    }
]

def map_regulations_to_compliance_points(regulations_json_path: str, output_path: str):
    with open(regulations_json_path, "r", encoding="utf-8") as f:
        clauses = json.load(f)

    compliance_points = []
    
    for rule in COMPLIANCE_RULES_MAP:
        # Match with clause in json
        matched_clause = None
        for c in clauses:
            fn = c["filename"].lower()
            sec = c["section"].lower()
            if rule["doc_match"] in fn and rule["section_match"].lower() in sec:
                matched_clause = c
                break
                
        point = {
            "rule_id": rule["rule_id"],
            "regulator": "SEBI",
            "document": matched_clause["document"] if matched_clause else rule["doc_match"],
            "filename": matched_clause["filename"] if matched_clause else "",
            "source_section": matched_clause["section"] if matched_clause else rule["section_match"],
            "page": matched_clause["page"] if matched_clause else 1,
            "compliance_point": rule["compliance_point"],
            "obligation_type": rule["obligation_type"],
            "risk_if_violated": rule["risk_if_violated"],
            "original_clause_text": matched_clause["text"] if matched_clause else ""
        }
        compliance_points.append(point)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(compliance_points, f, indent=2, ensure_ascii=False)

    print(f"--- Phase 3: Compliance Points Extraction Completed ---")
    print(f"Total Compliance Points Extracted: {len(compliance_points)}")
    print(f"Output saved to: {output_path}")
    
    # Summary of obligations
    type_counts = {}
    for p in compliance_points:
        t = p["obligation_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"Obligation Breakdown: {type_counts}")

if __name__ == "__main__":
    in_file = os.path.join("data", "processed", "regulations.json")
    out_file = os.path.join("data", "processed", "compliance_points.json")
    map_regulations_to_compliance_points(in_file, out_file)
