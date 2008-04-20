#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for `bobcatlib.preprocessor`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest, os
from bobcatlib import preprocessor
from bobcatlib.common import PositionMarker

suite = unittest.TestSuite()

class TestExcerpt(unittest.TestCase):
    """Abstract base class for all tests with `preprocessor.Excerpt`.

    :cvar sample_text: The encoded text that should be written to the testbed
      file.  Note that this is not a Unicode string but an octet string.  It
      must be specified in derived classes.
    :ivar text: the Bobcat source text that was read from the file
    :ivar encoding: the detected encoding of the Bobcat file
    :ivar bobcat_version: the detected Bobcat version of the Bobcat file

    :type sample_text: str
    :type text: `preprocessor.Excerpt`
    :type encoding: str
    :type bobcat_version: str"""
    def setUp(self):
        """Write a test Bobcat file to the testbed directory so that it can be
        read immediately, in order to create a `preprocessor.Excerpt` instance,
        and in order to be able to test the return values or
        `preprocessor.load_file`."""
        testfile = open("test.bcat", "w")
        testfile.write(self.sample_text)
        testfile.close()
        self.text, self.encoding, self.bobcat_version = preprocessor.load_file("test.bcat")
    def tearDown(self):
        """Remove the test Bobcat file from the testbed."""
        # Actually, this could also be removed already in `setUp` but here, I
        # find it more logical.  And who knows: Maybe it must be re-read.
        os.remove("test.bcat")

class TestExcerptSlicing(TestExcerpt):
    """Abstract base class for very basic tests with `preprocessor.Excerpt`:
    proper preprocessing, slicing, and concatenating.

    :cvar original_positions: the desired values for the original positions in
      the test excerpt, as to be used in `compare_original_positions`.  This
      must be set in a derived class.
    :cvar escaped_positions: the desired value for the escaped positions in the
      test excerpt.  This must be set in a derived class.

    :type original_positions: dict mapping int to `common.PositionMarker`
    :type escaped_positions: set of int
    """
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
        """General check whether the position markers within an excerpt are
        correct.  The method compares the desired and the actual value and
        generates detailed error messages if necessary.

        :Parameters:
          - `desired`: the to-be-expected position markers
          - `actual`: the actually found positon markers in the excerpt

        :type desired: dict mapping int to `common.PositionMarker`
        :type actual: dict mapping int to `common.PositionMarker`
        """
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
    """Test case class for basic tests with `preprocessor.Excerpt` *before*
    applying the post input method.
    """
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
    """Test case class for basic tests with `preprocessor.Excerpt` *after*
    applying the post input method.
    """
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
        """normal indexing (no slices) should work as with strings"""
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
    def shortDescription(self):
        """Additionally to the default message, we append a notice that this is
        about *postprocessed* excerpts here.
        """
        description = super(TestExcerptSlicingAfterPostprocessing, self).shortDescription()
        return (description or "") + " (after post input method applied)"

class TestExcerptSplit(TestExcerpt):
    """Test case for the method `preprocessor.Excerpt.split`.
    """
    sample_text = """.. -*- coding: utf-8 -*-
.. Bobcat 1.0
a, b, c,"""
    def test_split(self):
        """splitting of preprocessor.Excerpt into parts should work as with strings"""
        sliced_text = self.text[2:]
        parts = sliced_text.split(",")
        self.assertEqual(parts, [u'a', u' b', u' c', u''])
        self.assertEqual(parts[0].original_position(), PositionMarker("test.bcat", 3, 0, 0))
        parts = self.text.split()
        self.assertEqual(parts, [u'a,', u'b,', u'c,'])
        self.assertEqual(parts[1].original_position(), PositionMarker("test.bcat", 3, 3, 0))

class TestExcerptCodeSnippetsIntervals(TestExcerpt):
    """Test case for the handling of code snippets in `preprocessor.Excerpt`.
    They should be treated as escaped characters, and this is tested here.
    """
    sample_text = """.. -*- coding: utf-8 -*-
.. Bobcat 1.0
..

This is a code snippet: ```GOTO 10```.  And this is one in a paragraph of its
own:

```
GOTO 10
```

And here the file ends.
"""
    def test_preprocessing(self):
        """code snippets should be properly preprocessed"""
        self.assertEqual(self.text, "\n\n\n\nThis is a code snippet: ```GOTO 10```.  "
                         "And this is one in a paragraph of its\nown:\n\n```\nGOTO 10\n```"
                         "\n\nAnd here the file ends.\n")
        self.assertEqual(self.text.code_snippets_intervals, [(31, 38), (91, 100)])
    def test_slicing(self):
        """code snippet intervals should be splitted properly with slicing of """ \
            """preprocessor.Excerpt"""
        part1, part2 = self.text[:34], self.text[34:]
        self.assertEqual(part1.code_snippets_intervals, [(31, 34)])
        self.assertEqual(part2.code_snippets_intervals, [(0, 4), (57, 66)])
        self.assertEqual((part1+part2).code_snippets_intervals, [(31, 34), (34, 38), (91, 100)])
    def test_escaped_text(self):
        """code snippets should be treated as escaped text"""
        self.assertEqual(self.text.escaped_text(),
                         u"\n\n\n\nThis is a code snippet: ```\x00\x00\x00\x00\x00\x00\x00```.  "
                         u"And this is one in a paragraph of its\nown:\n\n```"
                         u"\x00\x00\x00\x00\x00\x00\x00\x00\x00```\n\nAnd here the file ends.\n")
        self.assertEqual(len(self.text.escaped_text()), len(self.text))

class TestExcerptCodeSnippetsIntervalsOpenEnding(TestExcerpt):
    """Test case for the special (unwanted, maybe illegal) case of a code
    snippet which is not closed in the Bobcat source file.
    """
    sample_text = """.. -*- coding: utf-8 -*-
.. Bobcat 1.0
..

This is a code snippet with open ending: ```GOTO 10
"""
    def test_processing(self):
        """upper bound of open-ending code snippet should be the end of the preprocessor.Excerpt"""
        self.assertEqual(len(self.text), self.text.code_snippets_intervals[0][1])

class TestExcerptNormalizeWhitespace(unittest.TestCase):
    """Test case for `preprocessor.Excerpt.normalize_whitespace`.
    """
    def test_normalize_whitespace(self):
        """preprocessor.Excerpt.normalize_whitespace should work as for strings"""
        excerpt = preprocessor.Excerpt(" a\tb\t c  d \n ef \tg \n ", "PRE", "test.bcat", {}, {})
        self.assertEqual(excerpt.normalize_whitespace(), u"a b c d ef g")
    def test_whitespace_only(self):
        """whitespace normalization for whitespace-only preprocessor.Excerpt should yield """ \
            """an empty preprocessor.Excerpt"""
        empty_excerpt = preprocessor.Excerpt(" \t\t    \n  \t \n ", "PRE", "test.bcat", {}, {}) \
            .normalize_whitespace()
        self.assertEqual(empty_excerpt, u"")
        self.assertEqual(empty_excerpt.original_position(0), PositionMarker("test.bcat", 1, 0, 0))

for test_class in (TestExcerptSlicingBeforePostprocessing,
                   TestExcerptSlicingAfterPostprocessing,
                   TestExcerptSplit,
                   TestExcerptCodeSnippetsIntervals,
                   TestExcerptCodeSnippetsIntervalsOpenEnding,
                   TestExcerptNormalizeWhitespace):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
