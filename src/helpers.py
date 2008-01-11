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

"""General helper routines for minor tasks or debugging purposes.  If a routine
should be available in (almost) all parts of Gummi, use the common module
instead."""

from common import Error, modulepath
import sys

def print_tree(tree, line_columns=(0,)):
    """Print a nested list of strings as an ASCII tree to stdout.  Example:

    >>> print_tree([["Peter", ["Ian", ["Randy", ["Clara"]]]], "Paul", ["Mary", ["Arthur"]]])
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

    :Parameters:
      - `tree`: A list of items.  Every item is either a string (then it is
        terminal) or a list of a string and its subtree.

    :type tree: list

    :Return:
      None

    """
    for i, item in enumerate(tree):
        current_line = u""
        last_pos = -1
        for pos in line_columns:
            current_line += (pos - last_pos - 1) * " " + "|"
            last_pos = pos
        print current_line
        if isinstance(item, list):
            print current_line[:-1] + "+---> " + item[0]
            new_line_columns = list(line_columns) + [line_columns[-1] + 6 + len(item[0]) // 2]
            if i == len(tree) - 1:
                del new_line_columns[-2]
            print_tree(item[1], new_line_columns)
        elif isinstance(item, basestring):
            print current_line[:-1] + "+---> " + item
        else:
            raise Error(u"Invalid type in tree: " + unicode(type(item)))

def import_local_module(name):
    """Load a module from the local Gummi modules directory.

    Loading e.g. the parser module is difficult because on Windows, the stdlib
    parser module is a built-in and thus loaded with higher priority.  And as
    long as http://www.python.org/dev/peps/pep-0328/ is not realised, I have to
    do it this way (or rename my parser.py, which I don't want to do).

    :Parameters:
      - `name`: name of the module, as it would be given to ``import``.

    :Return:
      the module object or ``None`` if none was found

    :rtype:
      module
    """
    # pylint: disable-msg=C0103
    import imp
    try:
        return sys.modules[name]
    except KeyError:
        fp, pathname, description = imp.find_module(name, [modulepath])
        try:
            return imp.load_module(name, fp, pathname, description)
        finally:
            # Since we may exit via an exception, close fp explicitly.
            if fp:
                fp.close()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
