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

"""The Gummi source document parser module.

Here, the input file is read in and transformed to an abstract syntax tree
(AST).  The nodes in this tree are objects, and they represent the objects in
the document: Section, paragraphs, tables etc.  Additionally, there is some
administrative stuff like meta data.  The classes defined here not only
represent a certain document structure, they also contain the code so parse
their region in the source document.  So in a way, the AST generates itself.

In the second phase, the AST can be told to create the output document (e.g. a
LaTeX file).  Then, the AST is walked through in a recursive manner and every
node generates ("emits") a certain fraction of output code.  This is realised
by code injection from the backend module into the classes of the parser.

This is the package initialisation file for the parser package.  It just
includes all parser components and exports them as if there was one big parser
module."""

import gummi.safefilename as _safefilename
from .common import (Node)
from .sectioning import (Document, Section, Heading)
from .basic_inline import (Emphasize, Text)
from .basic_block import (Paragraph)
from .xrefs import (Hyperlink, Footnote, FootnoteReference, DelayedWeblink, DelayedWeblinkReference)

import copy, inspect
_globals = copy.copy(globals())
Document.node_types = dict([(cls.__name__.lower(), cls) for cls in _globals.values()
                            if inspect.isclass(cls) and issubclass(cls, Node)])
del _globals, cls
