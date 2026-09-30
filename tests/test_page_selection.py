import unittest

from pdf_to_image.page_selection import PageSelectionError, parse_page_selection


class PageSelectionTests(unittest.TestCase):
    def test_parses_single_pages_and_ranges(self):
        self.assertEqual(parse_page_selection("1, 3, 5-8", 10), [1, 3, 5, 6, 7, 8])

    def test_keeps_first_occurrence_only(self):
        self.assertEqual(parse_page_selection("2, 2, 1-3", 5), [2, 1, 3])

    def test_rejects_page_outside_pdf(self):
        with self.assertRaises(PageSelectionError):
            parse_page_selection("1, 7", 6)

    def test_rejects_reverse_range(self):
        with self.assertRaises(PageSelectionError):
            parse_page_selection("5-2", 8)

    def test_rejects_blank_selection(self):
        with self.assertRaises(PageSelectionError):
            parse_page_selection("", 8)


if __name__ == "__main__":
    unittest.main()

