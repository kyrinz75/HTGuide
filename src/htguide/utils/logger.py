import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Tạo logger dùng chung cho toàn bộ project, tránh mỗi file tự cấu hình riêng."""
    logger = logging.getLogger(name)

    # Tránh add handler nhiều lần nếu get_logger được gọi lặp lại (vd khi import nhiều nơi)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Log ra console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger