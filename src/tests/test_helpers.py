# -*- coding: utf-8 -*-
# This file is Python 2.7.

"""Unit tests for `bobcatlib.helpers`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest, os
from bobcatlib import helpers, parser, preprocessor

suite = unittest.TestSuite()

class TestPrintTree(unittest.TestCase):
    """Test case for `helpers.print_tree`.
    """
    class Root: pass
    class Peter: pass
    class Ian: pass
    class Randy: pass
    class Clara: pass
    class Paul: pass
    class Mary: pass
    class Arthur: pass
    def test(self):
        """generating a printed tree for a given parse tree should work"""
        desired_result = u"""Root
  |
  +---> Peter
  |       |
  |       +---> Ian
  |       |
  |       +---> Randy
  |               |
  |               +---> Clara
  |
  +---> Paul
  |
  +---> Mary
          |
          +---> Arthur
"""
        self.assertEqual(
            helpers.print_tree([self.Root(), [[self.Peter(), [self.Ian(),
                                                              [self.Randy(),
                                                               [self.Clara()]]]],
                                              self.Paul(),
                                              [self.Mary(), [self.Arthur()]]]]), desired_result)
    def shortDescription(self):
        description = super(TestPrintTree, self).shortDescription()
        return "helpers.print_tree: " + (description or "")

class TestVisualizeTree(unittest.TestCase):
    """Test case for `helpers.visualize_tree`.
    """
    def setUp(self):
        open("test.bcat", "w").write(""".. -*- coding: utf-8 -*-
.. Bobcat 1.0

#. Introduction
===============

This is the _first_ paragraph.


#. Motivation
=============

This is the _second_ paragraph.

And this is the third one.


#.# Acknowledgements
====================

Yet _another_ text block.

And we go further and further.


#.#.# A subsubheading
=====================

"42" said Deep Thought, with infinite majesty and calm.

It was a long time before anyone spoke.


#. Last chapter
===============

This is almost the last paragraph.

And this is _definitely the last one_.
""")
        text, __, __ = preprocessor.load_file("test.bcat")
        self.document = parser.Document()
        self.document.parse(text)
    def test(self):
        """the plot generated with Graphviz from a given parse tree should be as expected"""
        helpers.visualize_tree(self.document.tree_list(), "test.canon")
        actual_result = open("test.canon").read()
        desired_result = open("test-desired.canon").read()
        self.assertEqual(actual_result, desired_result,
                         "Graphviz generated a plot which was different from the expected one")
    def tearDown(self):
        os.remove("test.bcat")
        os.remove("test.canon")
    def shortDescription(self):
        description = super(TestVisualizeTree, self).shortDescription()
        return "helpers.visualize_tree: " + (description or "")

for test_class in (TestPrintTree, TestVisualizeTree):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
