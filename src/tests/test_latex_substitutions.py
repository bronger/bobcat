#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for `bobcatlib.latex_substitutions`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest
from bobcatlib import latex_substitutions

suite = unittest.TestSuite()

class TestProcessTest(unittest.TestCase):
    """Test case for `latex_substitutions.process_text`."""
    def test(self):
        """converting a Unicode codepoint to a LaTeX macro should work"""
        self.assertEqual(latex_substitutions.process_text(u"→", "de", "TEXT"), ur"$\rightarrow${}")
        self.assertEqual(latex_substitutions.process_text(u"€", "de", "TEXT"), ur"\texteuro{}")
    def test_math(self):
        """converting a Unicode codepoint to a LaTeX macro in math mode should work"""
        self.assertEqual(latex_substitutions.process_text(u"a", "de", "MATH"), u"a")
        self.assertEqual(latex_substitutions.process_text(u"→", "de", "MATH"), ur"\rightarrow ")
        self.assertEqual(latex_substitutions.process_text(u"a→", "de", "MATH"), ur"a\rightarrow ")
        self.assertEqual(
            latex_substitutions.process_text(u"→→", "de", "MATH"), ur"\rightarrow \rightarrow ")
    def test_math_trailing(self):
        """converting a Unicode codepoint to a LaTeX macro in math mode with trailing letter """ \
            """should generate a space between them"""
        self.assertEqual(latex_substitutions.process_text(u"→x", "de", "MATH"), ur"\rightarrow x")
    def test_text_trailing(self):
        """converting a Unicode codepoint to a LaTeX macro in math mode with trailing sign """ \
            """should generate a space between them if and only if the following sign is a """ \
            """letter"""
        self.assertEqual(
            latex_substitutions.process_text(u"a€€a", "de", "TEXT"), ur"a\texteuro\texteuro a")
        self.assertEqual(latex_substitutions.process_text(u"a € € a", "de", "TEXT"),
                         ur"a \texteuro\ \texteuro\ a")
    def test_special_characters_text(self):
        """characters that have a special meaning in LaTeX should work in text mode"""
        self.assertEqual(
            latex_substitutions.process_text(u"!^°$%&{}\\`´?#~<>|'@"+'"', "de", "TEXT"),
            ur"!{}\textasciicircum\textdegree\textdollar\%\&\{\}\textbackslash"
            ur"`{}\textasciiacute?{}\#\textasciitilde<{}>{}|'{}@\char34{}")
    def test_special_characters_math(self):
        """characters that have a special meaning in LaTeX should work in math mode"""
        self.assertEqual(
            latex_substitutions.process_text(u"!^°$%&{}\\`´?#~<>|'@"+'"', "de", "MATH"),
            ur"!{\char94}^\circ \$\%\&\{ \} \backslash \grave{\hspace*{0.5em}} "
            ur"\acute{\hspace*{0.5em}} ?\#{\char126}<>|'@{\char34}")
    def shortDescription(self):
        description = super(TestProcessTest, self).shortDescription()
        return "latex_substitutions.process_test: " + (description or "")

for test_class in (TestProcessTest,):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
