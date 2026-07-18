from pathlib import Path

# Root của project (đi ngược từ file này lên 3 cấp: paths.py -> utils -> htguide -> src -> ROOT)
ROOT_DIR = Path(__file__).resolve().parents[3]

# Thư mục data
DATA_DIR = ROOT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_INTERIM_DIR = DATA_DIR / "interim"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# Thư mục con trong raw, theo loại file đã phân loại
PDF_TEXT_DIR = DATA_RAW_DIR / "pdf_text"
PDF_SCANNED_DIR = DATA_RAW_DIR / "pdf_scanned"
DOCX_DIR = DATA_RAW_DIR / "docx"

# Tự tạo thư mục nếu chưa tồn tại (an toàn khi chạy lần đầu)
for d in [PDF_TEXT_DIR, PDF_SCANNED_DIR, DOCX_DIR, DATA_INTERIM_DIR, DATA_PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)