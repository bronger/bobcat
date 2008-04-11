#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2007 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Gummi program.
#
#    Gummi is free software; you can redistribute it and/or modify it under
#    the terms of the MIT licence:
#
#    Permission is hereby granted, free of charge, to any person obtaining a
#    copy of this software and associated documentation files (the "Software"),
#    to deal in the Software without restriction, including without limitation
#    the rights to use, copy, modify, merge, publish, distribute, sublicense,
#    and/or sell copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#

from .common import guarded_match, guarded_search, guarded_find, Node
# FixMe: The following import should become relative.  At the moment, it can't
# due to <http://bugs.python.org/issue992389>.
import sectioning
from gummi.parser.basic_inline import parse_inline
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
