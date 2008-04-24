#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for `bobcatlib.i18n`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest, gettext, os
from bobcatlib import i18n, preprocessor

gettext._default_localedir = "locale"

suite = unittest.TestSuite()

class TestI18n(unittest.TestCase):
    def check_translation(self, text, language, desired_translation, strict=False):
        actual_translation = i18n.translate(text, language, strict)
        self.assertEqual(actual_translation, desired_translation)
        self.assert_(isinstance(actual_translation, unicode))
    def test_translate(self):
        """translation to arbitray languages should work"""
        self.check_translation(u"January", "de", u"Januar")
        self.check_translation(u"January", "de-at", u"Jänner")
    def test_strict_translations(self):
        """strict translations in languages without an .mo file should fallback to untranslated"""
        self.check_translation(u"January", "de-de", u"January", strict=True)
        self.check_translation(u"January", "de-de", u"Januar", strict=False)
    def test_fallback(self):
        """unfound translations in a language file should cause fallbacks to parental languages"""
        self.check_translation(u"kiss", "de-de-1901", u"Kuß")
        # The following causes the fallback to "de"
        self.check_translation(u"January", "de-de-1901", u"Januar")
    def test_fallback_strict(self):
        """strict translations in languages with an .mo file should fallback to parental """ \
            """languages"""
        self.check_translation(u"January", "de-ch", u"Januar", strict=True)
    def shortDescription(self):
        description = super(TestI18n, self).shortDescription()
        return "i18n.translate: " + (description or "")

class TestTranslations(unittest.TestCase):
    def test_translations(self):
        """third-party translations (e.g. backends) should work"""
        rtf_translations = i18n.Translations("rtf")
        self.assertEqual(rtf_translations.translate("Highway", "de"), u"Autobahn")
    def shortDescription(self):
        description = super(TestTranslations, self).shortDescription()
        return "i18n.Translations: " + (description or "")

class TestMatchLanguageDependently(unittest.TestCase):
    def setUp(self):
        self.filename = "test.bcat"
        open(self.filename, "w").write(
            ".. -*- coding: utf-8 -*-\n.. Bobcat 1.0\n\nJanuar\n\\January\n")
        self.text, __, __ = preprocessor.load_file(self.filename)
    def test_translated(self):
        """matching the translated version in the source should work"""
        self.assert_(i18n.match_language_dependently(u"January", self.text, 3, "de"))
    def test_translated_escaped(self):
        """matching the translated, escaped version in the source should fail or work """ \
            """according to the "unescaped_only" option"""
        self.assert_(not i18n.match_language_dependently(u"January", self.text, 10, "de"))
        self.assert_(
            i18n.match_language_dependently(u"January", self.text, 10, "de", unescaped_only=False))
    def test_without_mo_file(self):
        """matching the translated version in the source should fail if the target language """ \
            """doesn't have an ".mo" file"""
        self.assert_(not i18n.match_language_dependently(u"January", self.text, 3, "de-de"))
    def tearDown(self):
        os.remove(self.filename)
    def shortDescription(self):
        description = super(TestMatchLanguageDependently, self).shortDescription()
        return "i18n.match_language_dependently: " + (description or "")
        
for test_class in (TestI18n, TestTranslations, TestMatchLanguageDependently):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
