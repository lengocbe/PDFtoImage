"""Parsing and validation for PDF page selection strings."""


class PageSelectionError(ValueError):
    """Raised when a page selection cannot be interpreted safely."""


def parse_page_selection(selection: str, page_count: int) -> list[int]:
    """Return one-based page numbers from syntax such as ``1, 3, 5-8``.

    Values are returned in the order supplied, without duplicates.  All values
    must exist in the PDF, which prevents accidental partial conversions.
    """
    if page_count < 1:
        raise PageSelectionError("PDF không có trang nào để xuất.")
    if not selection or not selection.strip():
        raise PageSelectionError("Hãy nhập số trang cần xuất, ví dụ: 1, 3, 5-8.")

    pages: list[int] = []
    seen: set[int] = set()
    for raw_part in selection.split(","):
        part = raw_part.strip()
        if not part:
            raise PageSelectionError("Danh sách trang có mục trống.")
        if "-" in part:
            bounds = [value.strip() for value in part.split("-")]
            if len(bounds) != 2 or not all(value.isdigit() for value in bounds):
                raise PageSelectionError(f"Khoảng trang không hợp lệ: {part}")
            start, end = (int(value) for value in bounds)
            if start > end:
                raise PageSelectionError(f"Khoảng trang phải tăng dần: {part}")
            candidates = range(start, end + 1)
        else:
            if not part.isdigit():
                raise PageSelectionError(f"Số trang không hợp lệ: {part}")
            candidates = (int(part),)

        for page in candidates:
            if page < 1 or page > page_count:
                raise PageSelectionError(
                    f"Trang {page} không tồn tại. PDF này có {page_count} trang."
                )
            if page not in seen:
                seen.add(page)
                pages.append(page)
    return pages

