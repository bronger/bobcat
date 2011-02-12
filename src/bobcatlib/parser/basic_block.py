#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2007, 2008 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Bobcat program.
#
#    Bobcat is free software; you can use it, redistribute it and/or modify it
#    under the terms of the MIT license.
#
#    You should have received a copy of the MIT license with Bobcat.  If not,
#    see <http://bobcat.origo.ethz.ch/wiki/Licence>.
#

"""Very basic block-level parsing for Bobcat.  Here, I digest paragraph and
block content models.
"""

from .common import guarded_match, guarded_search, guarded_find, Node
# FixMe: The following import should become relative.  At the moment, it can't
# due to <http://bugs.python.org/issue992389>.
import sectioning
from .basic_inline import parse_inline
import re

empty_line_pattern = re.compile(r"\n[ \t\n]*\n")

def parse_blocks(parent, text, position):
    """Parse the source for block elements like sections or paragraphs and add
    those elements to the current parental node.

    :Parameters:
      - `parent`: the context node.  All nodes found in this part of the source
        code will get this node as their parent.
      - `text`: source document
      - `position`: starting position for parsing

    :type parent: `Node`
    :type text: `preprocessor.Excerpt`
    :type position: int

    :Return:
      The new current parsing position in the source.  It is the next character
      that should be parsed.

    :rtype: int
    """
    length = len(text)
    while position < length:
        block_boundary_match = guarded_search(empty_line_pattern, text, position)
        if block_boundary_match:
            block_end, next_block_start = block_boundary_match.span()
            if block_end == position:
                # Should happen *rarely*.  Position should be set to the
                # beginning of the next block, if possible.  However, at least
                # at the very start of the document it may happen.
                position = next_block_start
                continue
        else:
            block_end = next_block_start = length
        equation_line_match = \
            guarded_search(sectioning.Section.equation_line_pattern, text, position, block_end)
        if equation_line_match:
            assert isinstance(parent, (sectioning.Document, sectioning.Section))
            # Current block is a heading, so do a look-ahead to get the nesting
            # level
            if sectioning.Section.get_nesting_level(text, position) > parent.nesting_level:
                section = sectioning.Section(parent)
                position = section.parse(text, position, equation_line_match.span())
            else:
                return position
        else:
            # Ordinary paragraph
            paragraph = Paragraph(parent)
            position = paragraph.parse(text, position, block_end)
            position = next_block_start
    return position

class Paragraph(Node):
    """Class for single paragraphs of text."""
    def __init__(self, parent):
        super(Paragraph, self).__init__(parent)
    def parse(self, text, position, end):
        super(Paragraph, self).parse(text, position)
        return parse_inline(self, text, position, end)
