
import pypdf
import os

files = [
    "Procurement Agent Info (1).pdf",
    "Procurement Intelligence Agent (Information) (1).pdf",
    "Procurement Intelligence Agent - Scope of Work (1).pdf",
    "Tender & RFQ Information (2).pdf",
    "Tender & RFQ agent (2).pdf"
]

output_file = "analysis_raw.txt"

with open(output_file, "w", encoding="utf-8") as f:
    for filename in files:
        f.write(f"\n{'='*50}\n")
        f.write(f"FILE: {filename}\n")
        f.write(f"{'='*50}\n")
        try:
            reader = pypdf.PdfReader(filename)
            for page in reader.pages:
                f.write(page.extract_text() + "\n")
        except Exception as e:
            f.write(f"Error reading {filename}: {e}\n")

print(f"Extraction complete. Output saved to {output_file}")
