# -*- coding: utf-8 -*-
# This file is Python 2.7.
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

"""Very basic inline-level parsing for Bobcat.  Here, I digest the inline
content model and associated elements.  In particular, text nodes are treated
here.
"""

# FixMe: This import should be turned into "import *" once the fix for
# http://article.gmane.org/gmane.comp.python.python-3000.devel/12267 has
# arrived here.  (Probably not befor Python 3.0.)  Of course, the __all__
# attribute must be properly set in common.py.
from .common import (Node, guarded_search)
from . import maths
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

inline_delimiter = re.compile(ur"[_`{]|<(\w|[$%&/()=?{}\[\]*+~#;,:.-@|])+>", re.UNICODE)
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
            if position < delimiter_match.start():
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
            elif delimiter == "{":
                equation = maths.MathEquation(parent)
                position = equation.parse(text, position, end)
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
        if position >= len(text) or text[position] != "_":
            self.throw_parse_error("Emphasize text is not terminated in current block")
        return position + 1
