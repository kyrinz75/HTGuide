from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]

DATA_DIR = ROOT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_INTERIM_DIR = DATA_DIR / "interim"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

CHROMA_DIR = ROOT_DIR / "data" / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
PDF_TEXT_DIR = DATA_RAW_DIR / "pdf_text"
PDF_SCANNED_DIR = DATA_RAW_DIR / "pdf_scanned"
DOCX_DIR = DATA_RAW_DIR / "docx"

for d in [PDF_TEXT_DIR, PDF_SCANNED_DIR, DOCX_DIR, DATA_INTERIM_DIR, DATA_PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)