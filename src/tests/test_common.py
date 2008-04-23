#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for `bobcatlib.common`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest, os
from bobcatlib import common, preprocessor, parser, settings

suite = unittest.TestSuite()

class TestParseLocalVariables(unittest.TestCase):
    """Test case for `common.parse_local_variables`.
    """
    def test_valid_line(self):
        """parsing a valid local variables line should work"""
        self.assertEqual(common.parse_local_variables(".. -*- coding: utf-8; Blah: Blubb -*-\n"),
                         {"blah": "blubb", "coding": "utf-8"})
    def test_other_line(self):
        """trying to parse a line that doesn't look like a local variables line """ \
            """should yield an empty dictionary"""
        self.assertEqual(common.parse_local_variables("This is not a local variables line"), {})
    def test_other_line_forced(self):
        """trying to parse a line that doesn't look like a local variables line """ \
            """in forced mode should fail"""
        self.assertRaises(common.LocalVariablesError,
                          lambda: common.parse_local_variables(
                                  "This is not a local variables line", force=True))
    def test_malformed_key(self):
        """parsing a local variables line with a malformed key should fail"""
        self.assertRaises(common.LocalVariablesError, lambda: common.parse_local_variables(
                ".. -*- coding: utf-8;+ Blah: Blubb -*-\n"))
    def test_non_ascii(self):
        """trying to parse a local variables line with non-ASCII characters should fail"""
        self.assertRaises(common.LocalVariablesError, lambda: common.parse_local_variables(
                "; -*- codiöng: utf-8 -*-\n", comment_marker="(#|;)"))
    def test_other_common_markers(self):
        """parsing with an alternative comment marker should work"""
        self.assertEqual(common.parse_local_variables("; -*- coding: utf-8 -*-\n",
                                                      comment_marker="(#|;)"), {'coding': 'utf-8'})
    def shortDescription(self):
        description = super(TestParseLocalVariables, self).shortDescription()
        return "common.parse_local_variables: " + (description or "")

class TestAddParseError(unittest.TestCase):
    def setUp(self):
        testfile = open("test.bcat", "w")
        testfile.write(".. -*- coding: utf-8 -*-\n.. Bobcat 1.0\nDummy document.\n")
        testfile.close()
        text, __, __ = preprocessor.load_file("test.bcat")
        self.document = parser.Document()
        self.assertEqual(self.document.parse(text, 0), 18)
    def test_parse_error(self):
        """generating a parse error should result in the proper parse error object being """ \
            """appended to `common.ParseError.parse_errors`."""
        self.document.throw_parse_error("test error message")
        self.assertEqual(repr(common.ParseError.parse_errors),
                         '[<ParseError file "test.bcat", line 1, column 24>]')
        self.assertEqual(common.ParseError.parse_errors[0].position,
                         common.PositionMarker("test.bcat", 1, 24, 24))
        # Necessary because "index" is not tested by `PositionMarker.__cmp__`.
        self.assertEqual(common.ParseError.parse_errors[0].position.index, 24)
        self.assertEqual(unicode(common.ParseError.parse_errors[0]),
                         u'file "test.bcat", line 1, column 24: test error message')
    def tearDown(self):
        os.remove("test.bcat")
        del common.ParseError.parse_errors[:]
    def shortDescription(self):
        description = super(TestAddParseError, self).shortDescription()
        return "common.add_parse_error: " + (description or "")

for test_class in (TestParseLocalVariables, TestAddParseError):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
