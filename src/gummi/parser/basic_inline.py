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

from common import *
import re

class Text(Node):
    """Class for the always terminal text nodes in the AST.  Thus, their
    children list is always empty.

    :ivar text: the text of the Text node

    :type text: `preprocessor.Excerpt`
    """
    text = u""
    def __init__(self, parent):
        super(Text, self).__init__(parent)
    def parse(self, text, position, end):
        """Copy a slice of the source code into `text` and apply the post input
        method."""
        super(Text, self).parse(text, position)
        self.text = text[position:end].apply_postprocessing()
        return end
    def process(self):
        """Pass `text` to the emitter."""
        self.root().emit(self.text)

inline_delimiter = re.compile(ur"[_`]|<(\w|[$%&/()=?{}\[\]*+~#;,:.-@|])+>", re.UNICODE)
def parse_inline(parent, text, position, end):
    """Parse the source for inline elements like emphasize or footnode and add
    those elements to the current parental node.

    :Parameters:
      - `parent`: the context node.  All nodes found in this part of the source
        code will get this node as their parent.
      - `text`: source document
      - `position`: starting position for parsing
      - `end`: ending position for parsing

    :type parent: `Node`
    :type text: `preprocessor.Excerpt`
    :type position: int
    :type end: int

    :Return:
      The new current parsing position in the source.  It is the next character
      that should be parsed.

    :rtype: int
    """
    while position < end:
        delimiter_match = guarded_search(inline_delimiter, text, position, end)
        if delimiter_match:
            textnode = Text(parent)
            position = textnode.parse(text, position, delimiter_match.start())
            delimiter = delimiter_match.group()
            if delimiter == "_":
                if isinstance(parent, Emphasize):
                    return position
                else:
                    emphasize = Emphasize(parent)
                    position = emphasize.parse(text, position+1, end)
            elif delimiter.startswith("<"):
                hyperlink = Hyperlink(parent)
                position = hyperlink.parse(text, position, delimiter_match.end())
        else:
            textnode = Text(parent)
            position = textnode.parse(text, position, end)
    return position

class Emphasize(Node):
    r"""Class for emphasised inline material, like LaTeX's ``\emph``."""
    def __init__(self, parent):
        super(Emphasize, self).__init__(parent)
    def parse(self, text, position, end):
        super(Emphasize, self).parse(text, position)
        position = parse_inline(self, text, position, end)
        if text[position] != "_":
            self.throw_parse_error("Emphasize text is not terminated in current block")
        return position + 1
