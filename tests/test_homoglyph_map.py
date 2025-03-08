import unittest
from sanitext.homoglyph_map import get_homoglyph_replacement, HOMOGLYPH_MAP


class TestHomoglyphMap(unittest.TestCase):

    def test_known_mappings(self):
        """Test some known homoglyph mappings."""
        test_cases = {
            "À": "A",
            "é": "e",
            "Ø": "O",
            "Ⅵ": "VI",
            "×": "x",
            "—": "-",
            "“": '"',
            "’": "'",
        }
        for char, expected in test_cases.items():
            with self.subTest(char=char):
                self.assertEqual(get_homoglyph_replacement(char), expected)

    def test_identity_mappings(self):
        """Ensure ASCII characters remain unchanged."""
        ascii_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        for char in ascii_chars:
            with self.subTest(char=char):
                self.assertEqual(get_homoglyph_replacement(char), char)

    def test_unmapped_characters(self):
        """Test that unmapped characters return themselves."""
        unmapped_chars = ["∑", "∞", "🔥", "💀"]
        for char in unmapped_chars:
            with self.subTest(char=char):
                self.assertEqual(get_homoglyph_replacement(char), char)

    def test_homoglyph_dict_integrity(self):
        """Ensure all mapped characters exist in HOMOGLYPH_MAP."""
        for key, value in HOMOGLYPH_MAP.items():
            with self.subTest(key=key):
                self.assertIsInstance(key, str)
                self.assertIsInstance(value, str)
                self.assertGreater(len(value), 0)  # Ensures no empty mappings


if __name__ == "__main__":
    unittest.main()
