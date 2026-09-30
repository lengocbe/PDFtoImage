"""PDF rendering service, intentionally independent from the user interface."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import fitz  # PyMuPDF


class PdfConversionError(ValueError):
    """Raised for an unreadable or invalid PDF input."""


ProgressCallback = Callable[[int, int, Path], None]


def validate_pdf_path(path: str | Path) -> Path:
    source = Path(path)
    if not source.is_file():
        raise PdfConversionError("Không tìm thấy file PDF đã chọn.")
    if source.suffix.lower() != ".pdf":
        raise PdfConversionError("Chỉ hỗ trợ file PDF.")
    return source


def get_page_count(path: str | Path) -> int:
    source = validate_pdf_path(path)
    try:
        with fitz.open(source) as document:
            if document.needs_pass:
                raise PdfConversionError("PDF đang được đặt mật khẩu nên chưa thể xuất ảnh.")
            if document.page_count < 1:
                raise PdfConversionError("PDF không có trang nào để xuất.")
            return document.page_count
    except fitz.FileDataError as error:
        raise PdfConversionError("File đã chọn không phải PDF hợp lệ hoặc đã bị hỏng.") from error
    except RuntimeError as error:
        raise PdfConversionError(f"Không mở được PDF: {error}") from error


def convert_pages(
    pdf_path: str | Path,
    output_folder: str | Path,
    pages: list[int],
    image_format: str = "png",
    progress: ProgressCallback | None = None,
    dpi: int = 200,
) -> list[Path]:
    """Render selected one-based pages to separate images without touching the PDF."""
    source = validate_pdf_path(pdf_path)
    destination = Path(output_folder)
    if not destination.is_dir():
        raise PdfConversionError("Hãy chọn thư mục xuất hợp lệ.")
    if image_format.lower() not in {"png", "jpg"}:
        raise PdfConversionError("Định dạng ảnh phải là PNG hoặc JPG.")
    if dpi < 72:
        raise PdfConversionError("Chất lượng ảnh tối thiểu là 72 DPI.")
    if not pages:
        raise PdfConversionError("Chưa có trang nào để xuất.")

    output_format = image_format.lower()
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    created: list[Path] = []
    try:
        with fitz.open(source) as document:
            if document.needs_pass:
                raise PdfConversionError("PDF đang được đặt mật khẩu nên chưa thể xuất ảnh.")
            if document.page_count < 1:
                raise PdfConversionError("PDF không có trang nào để xuất.")
            for page_number in pages:
                if page_number < 1 or page_number > document.page_count:
                    raise PdfConversionError(f"Trang {page_number} không tồn tại trong PDF.")
            for index, page_number in enumerate(pages, start=1):
                page = document.load_page(page_number - 1)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                output = destination / f"trang_{index:03d}.{output_format}"
                if output_format == "png":
                    pixmap.save(output)
                else:
                    pixmap.save(output, output="jpeg", jpg_quality=92)
                created.append(output)
                if progress:
                    progress(index, len(pages), output)
    except fitz.FileDataError as error:
        raise PdfConversionError("File PDF không hợp lệ hoặc đã bị hỏng.") from error
    return created
