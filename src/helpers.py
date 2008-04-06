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
import sys, codecs, os, parser, subprocess, StringIO, textwrap

def print_tree(tree):
    """Print a nested list of classes as an ASCII tree to stdout.  Example:

    >>> class Root: pass
    >>> class Peter: pass
    >>> class Ian: pass
    >>> class Randy: pass
    >>> class Clara: pass
    >>> class Paul: pass
    >>> class Mary: pass
    >>> class Arthur: pass
    >>> print_tree([Root(), [[Peter(), [Ian(), [Randy(), [Clara()]]]], Paul(),
    ...                      [Mary(), [Arthur()]]]])
    Root
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
      - `tree`: A list of a class and its subtree.  The subtree consists of
        items.  Every item is either a class (then it is terminal) or again a
        list of a class and its subtree.  This parameter is created by
        `parser.Node.tree_list`.

    :type tree: list

    """
    def print_subtree(subtree, line_columns):
        """Here, the actual work is done.  In contrast to `print_tree`, this
        routine takes a list of child elements.  Actually, one should see it
        the other way round: `print_tree` is a front-end for this function that
        allows for giving a named root element, and that can digest the output
        of the `parser.Node.tree_list` function directly.
        
        :Parameters:
          - `subtree`: list of items.  Every item is either a string (then it
            is terminal) or a list of a string and its subtree.
          - `line_columns`: tuple of column numbers with the vertical lines

        :type subtree: list
        :type line_columns: tuple of int
        """
        for i, item in enumerate(subtree):
            current_line = u""
            last_pos = -1
            for pos in line_columns:
                current_line += (pos - last_pos - 1) * " " + "|"
                last_pos = pos
            print current_line
            if isinstance(item, list):
                itemname = item[0].__class__.__name__
                print current_line[:-1] + "+---> " + itemname
                new_line_columns = list(line_columns) + [line_columns[-1] + 6 + len(itemname) // 2]
                if i == len(subtree) - 1:
                    del new_line_columns[-2]
                print_subtree(item[1], new_line_columns)
            else:
                print current_line[:-1] + "+---> " + item.__class__.__name__
    assert isinstance(tree, list) and len(tree) == 2
    rootname = tree[0].__class__.__name__
    print rootname
    print_subtree(tree[1], (len(rootname)//2,))

def visualize_tree(tree, output_filename):
    """Creates an image file which visualises the document structure.  It
    relies on the dot program from the `Graphvis <http://www.graphviz.org/>`__
    package.

    :Parameters:
      - `tree`: A list of a class and its subtree.  The subtree consists of
        items.  Every item is either a class (then it is terminal) or again a
        list of a class and its subtree.  This parameter is created by
        `parser.Node.tree_list`.
      - `output_filename`: name of the output file.  The extension determines
        the file type.  Typical extensions are ``".eps"``, ``".gif"``, and
        ``".svg"``.  All possible output formats of Graphvis are supported.

    :Exceptions:
      - `common.Error`: if the dot program from the Graphviz package was not
        found.
    """
    colors = {"Section": "yellow", "Paragraph": "green", "Document": "red",
              "Heading": "goldenrod", "Emphasize": "darkseagreen2"}
    extension = os.path.splitext(output_filename)[1][1:]
    output_type = {"eps": "ps"}.get(extension, extension)
    output_encoding = {"ps": "latin-1"}.get(output_type, "utf-8")
    node_dict = {}
    def visualize_subtree(subtree):
        """Here, I generate the relationships of the nodes.  In particular, I
        don't generate the labels here."""
        def node_id(node):
            id_ = "Node" + str(id(node))
            node_dict[id_] = node
            return id_
        if subtree:
            for item in subtree[1]:
                line = "     " + node_id(subtree[0]) + " -> "
                if isinstance(item, list):
                    print>>output, line + node_id(item[0]) + " ;"
                    visualize_subtree(item)
                else:
                    print>>output, line + node_id(item) + " ;"
    try:
        dot_process = subprocess.Popen(["dot", "-T"+output_type, "-o", output_filename], stdin=subprocess.PIPE)
    except OSError:
        raise Error("could not start dot program")
    output = codecs.getwriter(output_encoding)(dot_process.stdin, errors="replace")
    print>>output, "digraph Bobcat_document"
    print>>output, "{"
    print>>output, 'ordering="out" ; node [fontname="Helvetica"] ;'
    visualize_subtree(tree)
    for id_, node in node_dict.iteritems():
        print>>output, "    ", id_, "[",
        is_text = isinstance(node, parser.Text)
        if is_text:
            text = node.text
            if text.startswith(" "):
                text = u"_" + text[1:]
            if text.endswith(" "):
                text = text[:-1] + u"_"
            text = u" ".join(text.split())
            if len(text) > 30:
                text = text[:29] + u"…" if output_encoding == "utf-8" else text[:27] + u"..."
            text = textwrap.fill(text, 10).replace("\n", "\\l")
            if "\\l" in text:
                text += "\\l"
            print>>output, u'label="' + text + '", shape="box", fontsize="12pt", fontname="Times-Roman"',
        else:
            classname = node.__class__.__name__
            print>>output, u"label=",
            print>>output, u'<<TABLE BGCOLOR="%s"><TR><TD>' % colors.get(classname, "yellow") + \
                classname + "</TD></TR>"
            for attribute in node.characteristic_attributes:
                name, human_name = \
                    attribute if isinstance(attribute, (tuple, list)) else 2 * (attribute,)
                print>>output, u'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10">%s: %s</FONT></TD></TR>' % \
                    (human_name, getattr(node, name))
            print>>output, u"</TABLE>>",
            print>>output, ', shape="plaintext"',
        print>>output, "] ;"
    print>>output, "}"
    # Send EOF through pipe, wait for process to terminate
    dot_process.communicate()

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
