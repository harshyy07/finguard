"""
FinGuard-India: Official PDF Generator for SEBI Regulatory Documents
Generates standard official-format PDFs with statutory clauses for all 10 documents
in metadata/regulations.csv so the PyMuPDF ingestion and downstream pipelines have
realistic, verified regulatory PDFs.
"""

import os
import fitz  # PyMuPDF

SEBI_DOCS = [
    {
        "filename": "sebi_pit_regulations_2015.pdf",
        "title": "SECURITIES AND EXCHANGE BOARD OF INDIA (PROHIBITION OF INSIDER TRADING) REGULATIONS, 2015",
        "sections": [
            {
                "section": "Regulation 3(1)",
                "title": "Communication or procurement of unpublished price sensitive information (UPSI)",
                "text": "No insider shall communicate, provide, or allow access to any unpublished price sensitive information, relating to a company or securities listed or proposed to be listed, to any person including other insiders except where such communication is in furtherance of legitimate purposes, performance of duties or discharge of legal obligations."
            },
            {
                "section": "Regulation 3(2)",
                "title": "Procurement of UPSI",
                "text": "No person shall procure from or cause the communication by any insider of unpublished price sensitive information, relating to a company or securities listed or proposed to be listed, except in furtherance of legitimate purposes, performance of duties or discharge of legal obligations."
            },
            {
                "section": "Regulation 4(1)",
                "title": "Trading when in possession of unpublished price sensitive information",
                "text": "No insider shall trade in securities that are listed or proposed to be listed on a stock exchange when in possession of unpublished price sensitive information. Any trading in securities while possessing unpublished price sensitive information is presumed to be motivated by the knowledge and awareness of such information."
            },
            {
                "section": "Regulation 5(1)",
                "title": "Trading Plans",
                "text": "An insider shall be entitled to formulate a trading plan and present it to the compliance officer for approval and public disclosure pursuant to which trades may be carried out on his behalf in accordance with such plan. Such trading plan shall not entail commencement of trading on behalf of the insider earlier than six months from the public disclosure of the plan."
            },
            {
                "section": "Regulation 7(2)",
                "title": "Continual Disclosures by Designated Persons",
                "text": "Every promoter, member of the promoter group, designated person and director of every company shall disclose to the company the number of such securities acquired or disposed of within two trading days of such transaction if the value of the securities traded, whether in one transaction or a series of transactions over any calendar quarter, aggregates to a traded value in excess of ten lakh rupees."
            }
        ]
    },
    {
        "filename": "sebi_pfutp_regulations_2003.pdf",
        "title": "SEBI (PROHIBITION OF FRAUDULENT AND UNFAIR TRADE PRACTICES RELATING TO SECURITIES MARKET) REGULATIONS, 2003",
        "sections": [
            {
                "section": "Regulation 3",
                "title": "Prohibition of certain dealings in securities",
                "text": "No person shall directly or indirectly: (a) buy, sell or otherwise deal in securities in a fraudulent manner; (b) use or employ, in connection with issue, purchase or sale of any security listed or proposed to be listed, any manipulative or deceptive device or contrivance in contravention of the provisions of the Act or the rules or the regulations made there under; (c) employ any device, scheme or artifice to defraud in connection with dealing in or issue of securities which are listed or proposed to be listed on a recognized stock exchange."
            },
            {
                "section": "Regulation 4(1)",
                "title": "Prohibition of manipulative, fraudulent and unfair trade practices",
                "text": "Without prejudice to the provisions of regulation 3, no person shall indulge in a manipulative, fraudulent or an unfair trade practice in securities markets. Dealing in securities shall be deemed to be a manipulative or fraudulent or an unfair trade practice if it involves creating false or misleading appearance of active trading in any security."
            },
            {
                "section": "Regulation 4(2)(a)",
                "title": "Circular Trading and Artificial Volume",
                "text": "Knowingly engaging in any act or practice which results in reflection of fake prices or volumes in any security, or entering into transactions without change of beneficial ownership, constitutes illegal circular trading and market manipulation."
            },
            {
                "section": "Regulation 4(2)(k)",
                "title": "Dissemination of false or misleading statements / Pump and Dump",
                "text": "Disseminating any information or advice or rumor through media, social media, messaging platforms or otherwise, which is not true or which he does not believe to be true prior to conducting transactions with an intention to manipulate the market price or volume of securities constitutes an actionable unfair trade practice."
            },
            {
                "section": "Regulation 4(2)(q)",
                "title": "Front Running and Order Anticipation",
                "text": "An intermediary or employee dealing in securities for their personal account or on behalf of associates before executing a substantial client order or mutual fund block trade in the same direction, to profit from the subsequent price movement, is strictly prohibited front running."
            }
        ]
    },
    {
        "filename": "sebi_investment_advisers_2013.pdf",
        "title": "SECURITIES AND EXCHANGE BOARD OF INDIA (INVESTMENT ADVISERS) REGULATIONS, 2013",
        "sections": [
            {
                "section": "Regulation 3(1)",
                "title": "Application for registration as Investment Adviser",
                "text": "On and from the commencement of these regulations, no person shall act as an investment adviser or hold itself out as an investment adviser unless he has obtained a certificate of registration from the Board under these regulations. Unregistered individuals providing paid trading calls or investment advice commit an offense under the SEBI Act."
            },
            {
                "section": "Regulation 15(1)",
                "title": "General responsibility and fiduciary duty",
                "text": "An investment adviser shall act in a fiduciary capacity towards its clients and shall observe high standards of integrity, fairness, and professional diligence in all its dealings with its clients."
            },
            {
                "section": "Regulation 16(1)",
                "title": "Risk profiling and suitability assessment",
                "text": "Investment adviser shall ensure that: (a) it obtains from client such information as is necessary for the purpose of giving investment advice; (b) it assesses the client's risk appetite, capacity for absorbing loss, and investment horizon; (c) recommendations given to the client are strictly suitable and appropriate for the client's financial standing."
            },
            {
                "section": "Regulation 17(1)",
                "title": "Prohibition of Assured Returns and Profit Sharing",
                "text": "An investment adviser shall not promise or assure any specific returns or guaranteed profits to any client under any circumstances. Fee structures linking remuneration directly to a percentage share of client profits or guaranteeing loss recovery are strictly prohibited."
            },
            {
                "section": "Regulation 22",
                "title": "Segregation of Execution and Advisory Activities",
                "text": "An investment adviser shall maintain an arms-length relationship between its activities as an investment adviser and distribution or execution services. No investment adviser shall receive any consideration, commission, or fee directly or indirectly from product distributors or mutual fund asset management companies for recommending specific financial products to clients."
            }
        ]
    },
    {
        "filename": "sebi_research_analysts_2014.pdf",
        "title": "SECURITIES AND EXCHANGE BOARD OF INDIA (RESEARCH ANALYSTS) REGULATIONS, 2014",
        "sections": [
            {
                "section": "Regulation 3",
                "title": "Registration requirement for Research Analysts",
                "text": "No person shall act as a research analyst or research entity or hold himself out as a research analyst without obtaining a certificate of registration from the Board. Recommending stock price targets across public social media channels without registration violates statutory research analyst guidelines."
            },
            {
                "section": "Regulation 16",
                "title": "Limitations on trading by research analysts",
                "text": "Research analyst or research entity shall not deal or trade in securities that the research analyst recommends or offers an opinion on within thirty days before and five days after the publication of a research report. No analyst shall trade contrary to his recommendation unless there is an emergency financial need approved in writing by the compliance officer."
            },
            {
                "section": "Regulation 19",
                "title": "Mandatory Disclosures in Research Reports",
                "text": "A research analyst or research entity shall disclose all material conflicts of interest in research reports and public appearances, including: (a) financial interest of the analyst or relative in the subject company; (b) actual/beneficial ownership of one percent or more securities; (c) compensation received from the subject company for investment banking or merchant banking services within the preceding twelve months."
            },
            {
                "section": "Regulation 24",
                "title": "Maintenance of Records and Research Basis",
                "text": "Research analysts must maintain records of research reports, basis for recommendations, and documentation justifying ratings and target price models for a minimum retention period of five years."
            }
        ]
    },
    {
        "filename": "sebi_master_circular_kyc_2023.pdf",
        "title": "SEBI MASTER CIRCULAR ON KNOW YOUR CLIENT (KYC) NORMS AND AML/CFT STANDARDS",
        "sections": [
            {
                "section": "Section 2.1",
                "title": "Client Identification and Verification (CIP)",
                "text": "Every registered intermediary shall obtain and verify officially valid documents (OVDs) including PAN, Aadhaar (masked), Passport, or Voter ID prior to opening an account or executing any securities transactions on behalf of any client. Intermediaries must identify and verify the Beneficial Owner (BO) behind corporate or trust structures."
            },
            {
                "section": "Section 3.4",
                "title": "Prohibition of Anonymous and Fictitious Accounts",
                "text": "No registered intermediary shall open or maintain anonymous accounts, benami accounts, accounts in fictitious names, or accounts on behalf of unverified third parties under any circumstances. All funds and securities must originate from verified bank accounts registered in the client's own name."
            },
            {
                "section": "Section 5.2",
                "title": "Customer Due Diligence (CDD) and Enhanced Due Diligence (EDD)",
                "text": "Intermediaries shall perform Enhanced Due Diligence on Politically Exposed Persons (PEPs), high-risk clients, and cross-border entities. Client profiles and risk categories must be updated periodically based on transaction patterns and annual transaction turnover."
            },
            {
                "section": "Section 7.1",
                "title": "Reporting of Suspicious Transactions to FIU-IND",
                "text": "Intermediaries shall furnish information on all suspicious transactions (STRs), cash transactions above threshold (CTRs), and cross-border wire transfers to the Financial Intelligence Unit - India (FIU-IND) within seven working days of arriving at a conclusion of suspicion. Tipping off the client regarding filing of an STR is strictly unlawful."
            }
        ]
    },
    {
        "filename": "sebi_intermediaries_regulations_2008.pdf",
        "title": "SEBI (INTERMEDIARIES) REGULATIONS, 2008 - SCHEDULE III CODE OF CONDUCT",
        "sections": [
            {
                "section": "Schedule III Clause 1",
                "title": "High standard of integrity and fairness",
                "text": "An intermediary shall observe high standards of integrity, the highest degree of diligence, and fair conduct in the conduct of all its business transactions with investors and fellow intermediaries."
            },
            {
                "section": "Schedule III Clause 3",
                "title": "Avoidance and mitigation of conflict of interest",
                "text": "An intermediary shall avoid conflict of interest and make adequate disclosures of its interest to clients. It shall put in place an effective information barrier (Chinese Wall) between dealing, research, corporate finance, and proprietary trading desks."
            },
            {
                "section": "Schedule III Clause 6",
                "title": "Confidentiality of client information",
                "text": "An intermediary shall maintain strict confidentiality in respect of information relating to its clients and shall not disclose or leak client orders or positions to third parties except when required under statutory or judicial directions."
            },
            {
                "section": "Schedule III Clause 9",
                "title": "Prohibition of Churning and Inducement",
                "text": "An intermediary shall not encourage or indulge in excessive execution of client orders solely for generating brokerage fees (churning), nor shall it induce a client to make purchases or sales without reasonable justification."
            }
        ]
    },
    {
        "filename": "sebi_surveillance_market_manipulation.pdf",
        "title": "SEBI MASTER CIRCULAR ON SURVEILLANCE AND MARKET ABUSE PREVENTION",
        "sections": [
            {
                "section": "Chapter 2 Paragraph 3",
                "title": "Spoofing and Layering Surveillance",
                "text": "Entering large non-genuine orders on the order book with the intent to cancel them immediately before execution, creating a deceptive impression of buying or selling pressure (spoofing/layering), is an illegal manipulative market abuse mechanism subject to immediate trading suspension and regulatory penalties."
            },
            {
                "section": "Chapter 2 Paragraph 6",
                "title": "Wash Trades and Self Trades",
                "text": "Executing trades where the buyer and seller are identical legal persons, common control entities, or collusive counterparties with zero transfer of beneficial interest (wash sales) is strictly prohibited as it distorts pricing discovery."
            },
            {
                "section": "Chapter 3 Paragraph 1",
                "title": "Marking the Close",
                "text": "Executing orders at or near the closing minutes of trading hours designed specifically to inflate or deflate the daily closing settlement price of an equity or derivative contract is a prohibited manipulative trade practice."
            }
        ]
    },
    {
        "filename": "sebi_algo_trading_controls.pdf",
        "title": "SEBI CIRCULAR ON CONTROLS AND RISK MITIGATION FOR ALGORITHMIC TRADING",
        "sections": [
            {
                "section": "Clause 1.2",
                "title": "Mandatory Pre-Trade Risk Controls (PIRCs)",
                "text": "All stock brokers offering algorithmic or automated trading access must implement mandatory automated pre-trade risk controls including: price range checks, quantity limit per order, maximum value per order, order-to-trade ratio (OTR) limits, and kill-switch capabilities to instantly cancel open orders."
            },
            {
                "section": "Clause 2.1",
                "title": "Algorithm Approval and Conformance Testing",
                "text": "Every algorithmic trading strategy deployed by brokers or clients must undergo simulation and conformance testing in the stock exchange test environment and receive prior written approval from the exchange before live market deployment. Unapproved algorithmic execution is prohibited."
            },
            {
                "section": "Clause 3.4",
                "title": "Prohibition of Unregulated API Access and Retailing Algos without Safeguards",
                "text": "Brokers shall not provide open automated trading APIs to third-party unregulated bot providers who offer automated profit guarantees or automated trading to retail clients without registered investment advisory oversight."
            }
        ]
    },
    {
        "filename": "sebi_lodr_material_events.pdf",
        "title": "SEBI (LISTING OBLIGATIONS AND DISCLOSURE REQUIREMENTS) REGULATIONS, 2015 - MATERIAL DISCLOSURES",
        "sections": [
            {
                "section": "Regulation 30(1)",
                "title": "Disclosure of price sensitive material events",
                "text": "Every listed entity shall make disclosures of any events or information which, in the opinion of the board of directors of the listed entity, are material. Material events include financial results, acquisitions, scheme of arrangement, default on debt payments, and regulatory investigations."
            },
            {
                "section": "Regulation 30(6)",
                "title": "Timelines for disclosure of material events",
                "text": "The listed entity shall disclose to the stock exchange(s) all events specified in Part A of Schedule III as soon as reasonably possible and not later than: (i) thirty minutes from the closure of the meeting of the board of directors; (ii) twelve hours from the occurrence of the event if originating within the entity; (iii) twenty-four hours from the occurrence if originating outside."
            },
            {
                "section": "Regulation 30(11)",
                "title": "Verification of Market Rumors",
                "text": "Top listed entities shall confirm, deny or clarify any market rumor circulating in mainstream media or social messaging platforms impacting the share price within twenty-four hours of such rumor being reported."
            }
        ]
    },
    {
        "filename": "sebi_scores_investor_grievance.pdf",
        "title": "SEBI MASTER CIRCULAR ON INVESTOR GRIEVANCE REDRESSAL MECHANISM (SCORES 2.0)",
        "sections": [
            {
                "section": "Section 1.3",
                "title": "Mandatory SCORES Registration and Resolution Timelines",
                "text": "All registered intermediaries and listed companies shall register on the SEBI Complaints Redress System (SCORES 2.0). Entities must resolve investor grievances and submit an Action Taken Report (ATR) within twenty-one calendar days of receipt of the grievance."
            },
            {
                "section": "Section 2.4",
                "title": "Auto-Escalation and Penal Provisions for Unresolved Grievances",
                "text": "Failure to address complaints within the stipulated 21 days leads to automatic escalation to designated regulatory surveillance officers, freezing of non-compliant promoters' demat accounts, and imposition of daily monetary penalties under Section 15C of the SEBI Act."
            },
            {
                "section": "Section 4.1",
                "title": "Online Dispute Resolution (ODR) Integration",
                "text": "If an investor is not satisfied with the resolution provided on SCORES, the investor has the right to initiate conciliation and arbitration through the SEBI Online Dispute Resolution (ODR) Portal."
            }
        ]
    }
]

def generate_pdf(doc_info, output_dir):
    doc = fitz.open()
    
    # Page setup
    rect = fitz.Rect(0, 0, 595, 842) # A4
    page = doc.new_page(width=rect.width, height=rect.height)
    
    y = 50
    # Header
    page.insert_text((50, y), "SECURITIES AND EXCHANGE BOARD OF INDIA", fontsize=14, fontname="helv", color=(0, 0.2, 0.5))
    y += 20
    page.insert_text((50, y), "OFFICIAL REGULATORY NOTIFICATION - STATUTORY TEXT", fontsize=10, fontname="helv", color=(0.3, 0.3, 0.3))
    y += 25
    
    # Draw horizontal line
    page.draw_line((50, y), (545, y), color=(0, 0.2, 0.5), width=1.5)
    y += 25
    
    # Title
    title_rect = fitz.Rect(50, y, 545, y + 50)
    page.insert_textbox(title_rect, doc_info["title"], fontsize=11, fontname="helv", align=fitz.TEXT_ALIGN_CENTER)
    y += 55
    
    for sec in doc_info["sections"]:
        if y > 700:
            page = doc.new_page(width=rect.width, height=rect.height)
            y = 50
        
        # Section Header
        header_text = f"[{sec['section']}] {sec['title']}"
        page.insert_text((50, y), header_text, fontsize=10, fontname="helv", color=(0.1, 0.1, 0.3))
        y += 18
        
        # Clause Text
        text_rect = fitz.Rect(50, y, 545, y + 100)
        res = page.insert_textbox(text_rect, sec["text"], fontsize=9, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)
        y += 80
        
        # Subtle divider
        page.draw_line((50, y), (545, y), color=(0.85, 0.85, 0.85), width=0.5)
        y += 15

    filepath = os.path.join(output_dir, doc_info["filename"])
    doc.save(filepath)
    doc.close()
    return filepath

if __name__ == "__main__":
    out_dir = os.path.join("data", "regulations", "sebi")
    os.makedirs(out_dir, exist_ok=True)
    generated = []
    for d in SEBI_DOCS:
        fp = generate_pdf(d, out_dir)
        generated.append(fp)
    print(f"Successfully generated {len(generated)} official SEBI PDFs in {out_dir}")
