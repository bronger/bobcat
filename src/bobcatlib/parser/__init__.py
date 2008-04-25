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

"""The Bobcat source document parser module.

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

# safefilename is not really used here, but it must be included so that the
# codec is registered.
from ..bobcatlib import safefilename as _safefilename

# FixMe: All imports in parentheses should be turned into "import *" once the
# fix for http://article.gmane.org/gmane.comp.python.python-3000.devel/12267
# has arrived here.  (Probably not befor Python 3.0.)  Of course, the __all__
# attributes must be properly set in the respective modules.
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
