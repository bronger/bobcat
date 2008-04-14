#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest, os
from bobcatlib import preprocessor
from bobcatlib.common import PositionMarker

suite = unittest.TestSuite()

class TextExcerpt(unittest.TestCase):
    def setUp(self):
        testfile = open("test.bcat", "w")
        testfile.write(self.sample_text)
        testfile.close()
        self.text, self.encoding, self.bobcat_version = preprocessor.load_file("test.bcat")
    def tearDown(self):
        os.remove("test.bcat")

class TestExcerptSlicing(TextExcerpt):
    sample_text = r""".. -*- coding: utf-8 -*-
.. Bobcat 1.0
.. \

\beta\
kf\0x64;sjh[[K2005]]\\56;fd\ \ \ kj
 \ \alpha--\ \alpha
\thetavar
\theta
"""
    def compare_original_positions(self, desired, actual):
        for position, marker in desired.iteritems():
            self.assert_(position in actual,
                         "missing PositionMarker <pos. %d, %s>" % (position, marker))
            self.assertEqual(marker, actual[position])
        for position, marker in actual.iteritems():
            self.assert_(position in desired,
                         "spurious extra PositionMarker <pos. %d, %s>" % (position, marker))
    def test_original_text(self):
        """preprocessor.Excerpts should store the correct original text"""
        self.assertEqual(self.text.original_text, self.sample_text)
    def test_original_positions(self):
        """preprocessor.Excerpts should find the correct original positions"""
        self.compare_original_positions(self.original_positions, self.text.original_positions)
    def test_escaped_positions(self):
        """preprocessor.Excerpts should find the correct escaped positions"""
        self.assertEqual(self.text.escaped_positions, self.escaped_positions)

class TestExcerptSlicingBeforePostprocessing(TestExcerptSlicing):
    original_positions = \
        {0: PositionMarker("test.bcat", 1, 24, 24),
         1: PositionMarker("test.bcat", 2, 13, 38),
         2: PositionMarker("test.bcat", 3, 4, 43),
         3: PositionMarker("test.bcat", 4, 0, 44),
         4: PositionMarker("test.bcat", 5, 0, 45),
         5: PositionMarker("test.bcat", 5, 6, 51),
         6: PositionMarker("test.bcat", 6, 0, 52),
         9: PositionMarker("test.bcat", 6, 8, 60),
         13: PositionMarker("test.bcat", 6, 13, 65),
         19: PositionMarker("test.bcat", 6, 20, 72),
         20: PositionMarker("test.bcat", 6, 22, 74),
         25: PositionMarker("test.bcat", 6, 33, 85),
         28: PositionMarker("test.bcat", 7, 0, 88),
         29: PositionMarker("test.bcat", 7, 3, 91),
         30: PositionMarker("test.bcat", 7, 9, 97),
         32: PositionMarker("test.bcat", 7, 13, 101),
         33: PositionMarker("test.bcat", 7, 19, 107),
         34: PositionMarker("test.bcat", 8, 0, 108),
         35: PositionMarker("test.bcat", 8, 6, 114),
         39: PositionMarker("test.bcat", 9, 0, 118),
         40: PositionMarker("test.bcat", 9, 6, 124),
         41: PositionMarker("test.bcat", 10, 0, 125)}
    escaped_positions = set([32, 6, 12, 18, 25, 29])
    def test_sourcecode_meta_data(self):
        """bobcatlib.preprocessor.load_file should load Bobcat files correctly"""
        self.assertEqual(self.text, u"\n\n\n\n\u03b2\nkfdsjh[K2005]\\56;fdkj\n \u03b1--\u03b1\n\u03b8var\n\u03b8\n")
        self.assertEqual(self.encoding, None)
        self.assertEqual(self.bobcat_version, "1.0")
    def test_slicing_with_negative_indices(self):
        """preprocessor.Excerpts should be slicable with negative and """ \
            """out-of-limits slice indices"""
        self.assertEqual(self.text[-100:-10], u"\n\n\n\n\u03b2\nkfdsjh[K2005]\\56;fdkj\n \u03b1-")
    def test_slicing_with_inverted_indices(self):
        """preprocessor.Excerpts should return empty slice if upper bound is """ \
            """lower than lower bound"""
        self.assertEqual(self.text[20:10], u"")

class TestExcerptSlicingAfterPostprocessing(TestExcerptSlicing):
    original_positions = \
        {0: PositionMarker("test.bcat", 1, 24, 24),
         1: PositionMarker("test.bcat", 2, 13, 38),
         2: PositionMarker("test.bcat", 3, 4, 43),
         3: PositionMarker("test.bcat", 4, 0, 44),
         4: PositionMarker("test.bcat", 5, 0, 45),
         5: PositionMarker("test.bcat", 5, 6, 51),
         6: PositionMarker("test.bcat", 6, 0, 52),
         32: PositionMarker("test.bcat", 7, 19, 107),
         9: PositionMarker("test.bcat", 6, 8, 60),
         39: PositionMarker("test.bcat", 9, 6, 124),
         13: PositionMarker("test.bcat", 6, 13, 65),
         34: PositionMarker("test.bcat", 8, 6, 114),
         19: PositionMarker("test.bcat", 6, 20, 72),
         20: PositionMarker("test.bcat", 6, 22, 74),
         25: PositionMarker("test.bcat", 6, 33, 85),
         33: PositionMarker("test.bcat", 8, 0, 108),
         38: PositionMarker("test.bcat", 9, 0, 118),
         28: PositionMarker("test.bcat", 7, 0, 88),
         29: PositionMarker("test.bcat", 7, 3, 91),
         30: PositionMarker("test.bcat", 7, 9, 97),
         31: PositionMarker("test.bcat", 7, 13, 101)}
    escaped_positions = set([6, 12, 18, 25, 29, 31])
    def setUp(self):
        super(TestExcerptSlicingAfterPostprocessing, self).setUp()
        self.text = self.text.apply_postprocessing()
    def test_slicing(self):
        """normal slicing and concatenating should work as with strings"""
        sliced_original_positions = {0: PositionMarker("test.bcat", 5, 0, 0),
                                     1: PositionMarker("test.bcat", 5, 6, 6),
                                     2: PositionMarker("test.bcat", 6, 0, 7),
                                     5: PositionMarker("test.bcat", 6, 8, 15),
                                     9: PositionMarker("test.bcat", 6, 13, 20),
                                     15: PositionMarker("test.bcat", 6, 20, 27),
                                     16: PositionMarker("test.bcat", 6, 22, 29)}
        sliced_escaped_positions = set([8, 2, 14])
        sliced_text = self.text[4:21]
        self.assertEqual(sliced_text, u"\u03b2\nkfdsjh[K2005]\\5")
        self.compare_original_positions(sliced_original_positions, sliced_text.original_positions)
        self.assertEqual(sliced_text.escaped_positions, sliced_escaped_positions)
        sliced_text = sliced_text[:10] + sliced_text[10:]
        self.assertEqual(sliced_text, u"\u03b2\nkfdsjh[K2005]\\5")
        self.assertEqual(sliced_text.original_text, u"\\beta\\\nkf\\0x64;sjh[[K2005]]\\\\5")
        self.compare_original_positions(sliced_original_positions, sliced_text.original_positions)
        self.assertEqual(sliced_text.escaped_positions, sliced_escaped_positions)
    def test_character_extraction(self):
        """"normal indexing (no slices) should work as with strings"""
        character = self.text[10]
        self.assertEqual(character, u"j")
        self.assertEqual(character.original_text, u"j")
        self.compare_original_positions({0: PositionMarker("test.bcat", 6, 9, 0)},
                                        character.original_positions)
        self.assertEqual(character.escaped_positions, set())
        sliced_text = character[10:]
        self.assertEqual(sliced_text, u"")
        self.assertEqual(sliced_text.original_text, u"")
        self.compare_original_positions({0: PositionMarker("test.bcat", 6, 10, 0)},
                                        sliced_text.original_positions)
        self.assertEqual(sliced_text.escaped_positions, set())
        self.assertRaises(IndexError, lambda: sliced_text[3])

suite.addTest(doctest.DocTestSuite("bobcatlib.preprocessor"))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(
        TestExcerptSlicingBeforePostprocessing))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(
        TestExcerptSlicingAfterPostprocessing))
suite.addTest(doctest.DocFileSuite("preprocessor.txt"))
