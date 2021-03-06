#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for `bobcatlib.safefilename`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest
from bobcatlib import safefilename

suite = unittest.TestSuite()

class TestEncoding(unittest.TestCase):
    """Test case for `safefilename.encode`.
    """
    def test_simple(self):
        """encoding a name with only ASCII letters should work"""
        encoded_name = u"hallo".encode("safefilename")
        self.assertEqual(encoded_name, "hallo")
        self.assert_(isinstance(encoded_name, str))
    def test_uppercase(self):
        """encoding a name with uppercase letter should work"""
        self.assertEqual(u"Hallo".encode("safefilename"), "{h}allo")
    def test_spaces(self):
        """encoding a name with spaces should work"""
        self.assertEqual(u"MIT Thesis".encode("safefilename"), "{mit}_{t}hesis")
    def test_umlauts(self):
        """encoding a name with umlauts and non-Latin-1 characters should work"""
        self.assertEqual(u"Geschäftsbrief".encode("safefilename"), "{g}esch(e4)ftsbrief")
        self.assertEqual(u"Geschαftsbrief".encode("safefilename"), "{g}esch(3b1)ftsbrief")
    def shortDescription(self):
        description = super(TestEncoding, self).shortDescription()
        return "safefilename.encode: " + (description or "")

class TestDecoding(unittest.TestCase):
    """Test case for `safefilename.decode`.
    """
    def test_umlauts(self):
        """decoding a filename with encoded umlauts and non-Latin-1 characters should work"""
        result = "{g}esch(e4)ftsbrief".decode("safefilename")
        self.assertEqual(result, u"Geschäftsbrief")
        self.assert_(isinstance(result, unicode))
        self.assertEqual(u"{g}esch(3b1)ftsbrief".decode("safefilename"), u"Geschαftsbrief")
    def test_uppercase_and_spaces(self):
        """decoding a filename with encoded uppercase letters and spaces should work"""
        self.assertEqual(u"{mit}_{t}hesis".decode("safefilename"), u"MIT Thesis")
    def test_unclosed_brace(self):
        """decoding a filename with an unclosed curly brace should fail"""
        self.assertRaises(UnicodeDecodeError, lambda: "{a".decode("safefilename"))
    def test_unmatched_parenthesis(self):
        """decoding a filename with an unmatched parenthesis should fail"""
        self.assertRaises(UnicodeDecodeError, lambda: "1(5g2".decode("safefilename"))
    def test_parentheses_with_invalid_code(self):
        """decoding a filename with parentheses containing invalid code should fail"""
        self.assertRaises(UnicodeDecodeError, lambda: "1(5g)2".decode("safefilename"))
    def test_uppercase_within_braces(self):
        """decoding a filename with an uppercase letter in curly braces should fail"""
        self.assertRaises(UnicodeDecodeError, lambda: "{H}allo".decode("safefilename"))
    def test_invalid_character(self):
        """decoding a filename with an invalid character should fail"""
        self.assertRaises(UnicodeDecodeError, lambda: "}allo".decode("safefilename"))
        self.assertRaises(UnicodeDecodeError, lambda: ")allo".decode("safefilename"))
        self.assertRaises(UnicodeDecodeError, lambda: chr(170)+"allo".decode("safefilename"))
    def test_errors_replace(self):
        """decoding a filename with errors="replace" should work"""
        self.assertEqual(u"{H}allo".decode("safefilename", "replace"), u"??allo")
        self.assertEqual(u"{".decode("safefilename", "replace"), u"")
        self.assertEqual(u"{Aallo".decode("safefilename", "replace"), u"?allo")
        self.assertEqual(u"1(rt)2".decode("safefilename", "replace"), u"1?2")
        self.assertEqual(u"1(rt2".decode("safefilename", "replace"), u"1?rt2")
    def test_errors_ignore(self):
        """decoding a filename with errors="ignore" should work"""
        self.assertEqual(u"{H}allo".decode("safefilename", "ignore"), u"allo")
        self.assertEqual(u"{allo".decode("safefilename", "ignore"), u"ALLO")
        self.assertEqual(u"{Aallo".decode("safefilename", "ignore"), u"allo")
        self.assertEqual(u"1(rt)2".decode("safefilename", "ignore"), u"12")
        self.assertEqual(u"1(rt2".decode("safefilename", "ignore"), u"1rt2")
    def shortDescription(self):
        description = super(TestDecoding, self).shortDescription()
        return "safefilename.decode: " + (description or "")

for test_class in (TestEncoding, TestDecoding):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
