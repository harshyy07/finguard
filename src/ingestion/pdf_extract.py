"""
FinGuard-India Phase 2: PDF Extraction and Cleaning Pipeline
Uses PyMuPDF to extract text from official SEBI regulation PDFs, preserves
section numbers, headings, clause boundaries, and page numbers, removes headers/footers,
and produces structured JSON with quality check metrics.
"""

import os
import re
import json
import csv
import pymupdf

def clean_extracted_text(text: str) -> str:
    """Remove redundant headers, footers, and normalize whitespace."""
    # Filter header lines
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Drop standard header/footer boilerplate
        if "SECURITIES AND EXCHANGE BOARD OF INDIA" in stripped:
            continue
        if "OFFICIAL REGULATORY NOTIFICATION" in stripped:
            continue
        if re.match(r"^Page\s+\d+(\s+of\s+\d+)?$", stripped, re.IGNORECASE):
            continue
        if stripped:
            cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)

def extract_pdf_clauses(pdf_path: str, doc_metadata: dict) -> list[dict]:
    """
    Extracts individual clauses and sections from a PDF while preserving
    page number, section identifiers, headings, and clean text.
    """
    doc = pymupdf.open(pdf_path)
    extracted_clauses = []
    
    current_doc_title = doc_metadata.get("title", os.path.basename(pdf_path))
    regulator = doc_metadata.get("regulator", "SEBI")
    source_url = doc_metadata.get("url", "")
    
    # Pattern for section markers: e.g. [Regulation 3(1)], [Section 2.1], [Schedule III Clause 1]
    section_pattern = re.compile(r"^\[(.*?)\]\s*(.*)$")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        raw_text = page.get_text("text")
        cleaned_text = clean_extracted_text(raw_text)
        
        # Split into blocks based on section tags
        lines = cleaned_text.split("\n")
        current_section = None
        current_heading = None
        current_clause_lines = []
        
        for line in lines:
            match = section_pattern.match(line)
            if match:
                # Save previous clause if present
                if current_section and current_clause_lines:
                    clause_text = " ".join(current_clause_lines).strip()
                    extracted_clauses.append({
                        "regulator": regulator,
                        "document": current_doc_title,
                        "filename": os.path.basename(pdf_path),
                        "section": current_section,
                        "heading": current_heading,
                        "page": page_num + 1,
                        "text": clause_text,
                        "source_url": source_url,
                        "char_count": len(clause_text)
                    })
                    current_clause_lines = []
                
                current_section = match.group(1).strip()
                current_heading = match.group(2).strip()
            else:
                if current_section:
                    current_clause_lines.append(line)
                    
        # Save trailing clause
        if current_section and current_clause_lines:
            clause_text = " ".join(current_clause_lines).strip()
            extracted_clauses.append({
                "regulator": regulator,
                "document": current_doc_title,
                "filename": os.path.basename(pdf_path),
                "section": current_section,
                "heading": current_heading,
                "page": page_num + 1,
                "text": clause_text,
                "source_url": source_url,
                "char_count": len(clause_text)
            })

    doc.close()
    return extracted_clauses

def run_extraction_pipeline(regulations_dir: str, metadata_csv: str, output_json: str):
    # Load metadata
    metadata_map = {}
    with open(metadata_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metadata_map[row["file"]] = row

    all_extracted_records = []
    print(f"--- Phase 2: Extracting from {regulations_dir} ---")
    
    for filename in sorted(os.listdir(regulations_dir)):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(regulations_dir, filename)
            meta = metadata_map.get(filename, {})
            records = extract_pdf_clauses(pdf_path, meta)
            print(f"Extracted {len(records):02d} clauses from: {filename}")
            all_extracted_records.extend(records)

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_extracted_records, f, indent=2, ensure_ascii=False)

    print(f"\n[Quality Check Report]")
    print(f"Total Documents Processed: {len(os.listdir(regulations_dir))}")
    print(f"Total Structured Clauses Extracted: {len(all_extracted_records)}")
    print(f"Saved cleanly to: {output_json}")

    # Inspect sample clauses
    print("\n--- Sample Extracted Clauses (Verification) ---")
    for sample in all_extracted_records[:3]:
        print(f"Doc: {sample['document'][:40]}... | Section: {sample['section']} | Page: {sample['page']}")
        print(f"Text Snippet: {sample['text'][:120]}...\n")

if __name__ == "__main__":
    reg_dir = os.path.join("data", "regulations", "sebi")
    meta_path = os.path.join("metadata", "regulations.csv")
    out_path = os.path.join("data", "processed", "regulations.json")
    run_extraction_pipeline(reg_dir, meta_path, out_path)
