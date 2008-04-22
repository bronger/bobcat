#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import common

suite = unittest.TestSuite()

class TestParseLocalVariables(unittest.TestCase):
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

for test_class in (TestParseLocalVariables,):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
