"""Check locale selection and parity of the compiled CLI recovery catalogs."""

import gettext
import os
import string
import unittest
from pathlib import Path
from unittest.mock import patch

from task_completion_detector.i18n import translate


class TranslationTests(unittest.TestCase):
    """Require complete English/German messages and compatible placeholders."""

    def test_catalog_keys_and_placeholders_match(self) -> None:
        catalogs = []
        locale_dir = Path(__file__).parents[1] / "task_completion_detector" / "locales"
        for language in ("en", "de"):
            messages = gettext.translation("messages", str(locale_dir), languages=[language])
            catalogs.append({key: value for key, value in messages._catalog.items() if key})
        self.assertEqual(set(catalogs[0]), set(catalogs[1]))
        formatter = string.Formatter()
        for key in catalogs[0]:
            with self.subTest(key=key):
                placeholders = [
                    {field for _, field, _, _ in formatter.parse(catalog[key]) if field}
                    for catalog in catalogs
                ]
                self.assertEqual(placeholders[0], placeholders[1])
                self.assertTrue(all(catalog[key] != key for catalog in catalogs))

    def test_locale_selection_and_english_fallback(self) -> None:
        for environment, expected in (
            ({"LANGUAGE": "de"}, "Bildschirmaufnahme"),
            ({"LC_ALL": "de_DE.UTF-8"}, "Bildschirmaufnahme"),
            ({"LANGUAGE": "fr:de"}, "Bildschirmaufnahme"),
            ({"LANGUAGE": "fr"}, "Screen Recording"),
            ({"LANG": "C"}, "Screen Recording"),
        ):
            with self.subTest(environment=environment):
                with patch.dict(os.environ, environment, clear=True):
                    self.assertIn(expected, translate("capture.macos_permission"))


if __name__ == "__main__":
    unittest.main()
