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

:var empty_line_pattern: pattern for empty lines in the source code
:var float_line_pattern: pattern for floats introducing lines in the source
  code
:var inline_delimiter: pattern for inline start delimiters

:type empty_line_pattern: re.pattern
:type float_line_pattern: re.pattern
:type inline_delimiter: re.pattern
"""

import re, weakref, imp, os.path
import common

# safefilename is not really used here, but it must be included so that the
# codec is registered.
import safefilename

def guarded_match(pattern, excerpt, pos=0):
    """Does a regexp match, avoiding any escaped characters in the match.

    :Parameters:
      - `pattern`: compiled regexp pattern
      - `excerpt`: excerpt of text that should be matched
      - `pos`: starting position of the match

    :type pattern: re.pattern
    :type excerpt: preprocessor.Excerpt
    :type pos: int

    :Return:
      The match object.  If no match was found, `None`.

    :rtype: re.match
    """
    return pattern.match(excerpt.escaped_text(), pos)

def guarded_search(pattern, excerpt, pos=0, endpos=None):
    """Does a regexp search, avoiding any escaped characters in the match.

    :Parameters:
      - `pattern`: compiled regexp pattern
      - `excerpt`: excerpt of text that should be searched
      - `pos`: starting position of the search
      - `endpos`: ending position for the search

    :type pattern: re.pattern
    :type excerpt: preprocessor.Excerpt
    :type pos: int
    :type endpos: int

    :Return:
      The match object.  If no match was found, `None`.

    :rtype: re.match
    """
    if endpos == None:
        return pattern.search(excerpt.escaped_text(), pos)
    else:
        return pattern.search(excerpt.escaped_text(), pos, endpos)

def guarded_find(substring, excerpt, pos=0, endpos=None):
    """Searches for a substring in an excerpt.

    :Parameters:
      - `substring`: substring that should be looked for
      - `excerpt`: excerpt of text that should be searched
      - `pos`: starting position of the search
      - `endpos`: ending position for the search

    :type substring: unicode
    :type excerpt: preprocessor.Excerpt
    :type pos: int
    :type endpos: int

    :Return:
      The index of the first occurence of `substring` in `excerpt`.  `None` if
      the substring was not found.

    :rtype: int
    """
    if endpos == None:
        result = excerpt.escaped_text().find(substring, pos)
    else:
        result = excerpt.escaped_text().find(substring, pos, endpos)
    if result == -1:
        result = None
    return result

class Node(object):
    """Abstract base class for all elements in the AST.  It will never be
    instantiated itself, only derived classes.  So it only defines the
    interface, most notably `children`, `parse`, `process_children`, `process`,
    and -- for debugging purposes -- `tree_list`.

    :ivar parent: the parent of this AST node.  This is not the mother class
      but the parent in the document.  The parent of a subsection is a section,
      for example.  Note that this is only a weak reference, so you must write
      `self.parent()` for getting the parent.

    :ivar root: the root element of this AST.  It must be of type `Document`.
      Note that this is only a weak reference, so you must write `self.root()`
      for getting the parent.

    :ivar children: all children nodes of this node.  Order is significant.

    :ivar language: the :RFC:`4646` language tag for this node.  Always in
      lowercase.

    :type parent: weakref to Node
    :type root: weakref to Node
    :type children: list of Nodes
    :type language: str
    """
    def __init__(self, parent):
        """It will also be called by all derived classes.

        :Parameters:
          - `parent`: parent node in the AST.  If `None`, it is the document
            root node.

        :type parent: Node
        """
        if parent:
            self.parent = weakref.ref(parent)
            self.root = parent.root
            # The order of the following two lines is important because
            # otherwise, ``self.root().current_language`` would return ``None``
            # for the very first child in the document node.
            parent.children.append(self)
            self.language = self.root().current_language
        else:
            # This is the root node
            self.parent = None
            self.language = None
        self.children = []
    def parse(self, text, position):
        u"""Parse a part of the source document and interpret it as the source
        representation of the current node.  Construct the current node and in
        particular its children according to that representation.

        :Parameters:
          - `text`: source document
          - `position`: starting position of the parsing

        :type text: preprocessor.Excerpt
        :type position: int

        :Return:
          The new position in the source document, i.e. the starting position
          of the following document part.  For example, for an emphasise node
          which is enclosed in underscores ``_…_``, it is the very next
          character position after the second underscore.

        :rtype: int
        """
        # pylint: disable-msg=R0201,W0613
        return position
    def __str__(self):
        """Serves debugging purposes only.  Consider using `tree_list()` and
        `helpers.print_tree()` instead."""
        return self.__repr__()
    def __repr__(self):
        """Serves debugging purposes only.  Consider using `tree_list()` and
        `helpers.print_tree()` instead."""
        return self.__class__.__name__ + "()"
    def tree_list(self):
        """Returns the current node and its children in a format suitable for
        `helpers.print_tree()`.

        :Return:
          A (nested) list of strings to be used in `helpers.print_tree`.

        :rtype: list
        """
        return [str(self.__class__).split(".")[1][:-2], \
                    [child.tree_list() for child in self.children]]
    def process(self):
        """Convert this node to backend output.  Typically, this routine will
        be overridden by backend functions so that the nodes emit code that
        suits to the respective backend.  For example, if the LaTeX backend is
        active, this process method will be replaced with a method that
        produces a LaTeX representation of the current node.

        However, if it is not overridden, it has a straightforward default
        behaviour: it passes the call to all of its children.  This default
        behaviour is defined here.

        It will be called when the AST is complete and the backend has injected
        its routines into the parser classes."""
        self.process_children()
    def process_children(self):
        """Call the `process` method of all of the Node's children.  It should
        never be overridden."""
        for child in self.children:
            child.process()

class Document(Node):
    """The root node of a document.

    There is always exactly one Document node in a Gummi AST, and this is the
    top node.  This is not the only thing which is special about it: It also
    contains variables which are "global" to the whole document.  It also
    contains special methods which are  used when the whole AST is finished and
    the actual output should be prepared.  These methods are called from the
    main program.

    :ivar root: Just for completeness, this always points to itself.  It is a
      weak reference.
    :ivar parent: This is always `None`.
    :ivar nesting_level: This is always -2.  It serves to mimic `Section`
      behaviour to other sections that want to know the nesting level of their
      parent section.
    :ivar languages: all languages that have been used in the document, as
      :RFC:`4646` strings.
    :ivar packages: set of features needed by this document, e.g. tables,
      formulae etc.  This can be used by the LaTeX backend to decide which
      additional packages must be included.  Normally, it simply contains LaTeX
      package names, but maybe RTF or OpenDocument need further possible items
      in this set.
    :ivar emit: `emitter.Emitter` object used for generating output.  Only
      `Document` and `Text` need `emit` of all routines in this module.
    :cvar node_types: dict which maps `Node` type names to the actual classes.

    :type parent: weakref to Node
    :type root: weakref to Node
    :type nesting_level: int
    :type languages: set
    :type packages: set of str
    :type node_types: dict
    :type emit: emitter.Emitter
    """
    node_types = {}
    def __init__(self):
        super(Document, self).__init__(None)
        self.__current_language = None
        self.languages = set()
        self.root = weakref.ref(self)
        self.nesting_level = -2
        self.packages = set()
        self.emit = None
    def parse(self, text, position=0):
        position = parse_blocks(self, text, position)
        self.language = self.language or "en"
        return position
    @staticmethod
    def find_backend(settings):
        """Find the file which contains the given backend, load it as a Python module,
        and return this module.  It is needed only by `generate_output`.

        :Parameters:
          - `settings`: The dict containing the settings intended for the backend

        :type settings: dict

        :Return:
          the backend module

        :rtype: module
        """
        # FixMe: This path should be made more flexible; the themes needn't be
        # next to the Python source scripts
        backend_name = settings["backend"]
        theme_path = os.path.normpath(os.path.join(common.modulepath, "..", "backends",
                                                   settings["theme"].encode("safefilename")))
        file_, pathname, description = imp.find_module(backend_name, [theme_path])
        try:
            backend_module = imp.load_module(backend_name, file_, pathname, description)
        finally:
            if file_:
                file_.close()
        return backend_module
    def generate_output(self):
        """Do everything needed for generating the final output of the
        conversion, for example, generate the LaTeX file.  It is called by the
        main program when the whole AST is finished.

        It registers the backend by loading its module and overwriting the
        `process` methods of certain node types with functions defined in the
        backend.  Futher, it copies the emitter called ``emit``, as defined in
        the backend, into this instance.  (This is necessary because one node
        type needs the emitter even in its un-overwritten form, namely `Text`,
        and otherwise, it would be necessary to define a new `Text.process`
        method in each backend.)
        """
        # FixMe: Here, the settings from the metainfo in the document must be
        # added to `settings`.  For now, I just add the theme because it is
        # important and won't be given on the command line.
        common.settings["theme"] = "Standard"
        backend_module = self.find_backend(common.settings)
        # Bidirectional code injection.  Only `Document` and `Text` need `emit`
        # of all parser.py routines.
        self.emit = backend_module.emit
        self.emit.set_settings(common.settings)
        prefix = "process_"
        process_functions = [name for name in backend_module.__dict__ if name.startswith(prefix)]
        assert self.node_types
        for function_name in process_functions:
            self.node_types[function_name[len(prefix):]].process = \
                backend_module.__dict__[function_name]
        self.process()
        self.emit.do_final_processing()
    def __get_current_language(self):
        if not self.__current_language and self.children:
            # The first text-generating element was created, and now it wants
            # to know the current language
            self.__current_language = self.language = "en"
            self.languages.add(self.__current_language)
        return self.__current_language
    def __set_current_language(self, current_language):
        self.__current_language = current_language.lower()
        if not hasattr(self, "language"):
            # Before any node-generating Gummi code, there was a language
            # directive
            self.language = self.__current_language
        self.languages.add(self.__current_language)
    current_language = property(__get_current_language, __set_current_language,
                                doc="""Current human language in the document.

    It is given in the :RFC:`4646` form.  This includes that it must be treated
    case-insensitively, therefore, it is stored with all-lowercase, no matter
    how it was given.

    :type: str
    """)


float_line_pattern = re.compile(r"^[ \t]*/{4,}[ \t]*$", re.MULTILINE)

class Text(Node):
    """Class for the always terminal text nodes in the AST.  Thus, their
    children list is always empty.

    :ivar text: the text of the Text node

    :type text: `preprocessor.Excerpt`
    """
    def __init__(self, parent):
        super(Text, self).__init__(parent)
    def parse(self, text, position, end):
        """Just copy a slice of the source code into `text`."""
        self.text = text[position:end]
        return end
    def process(self):
        """Pass `text` to the emitter.  Note that if you want to override this method
        in the backend, you must apply the postprocessing with
        `preprocessor.Excerpt.apply_postprocessing`."""
        self.root().emit(self.text.apply_postprocessing())

inline_delimiter = re.compile(r"[_]")
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
            position = delimiter_match.end()
            delimiter = delimiter_match.group()
            if delimiter == "_":
                emphasize = Emphasize(parent)
                position = emphasize.parse(text, position, end)
        else:
            textnode = Text(parent)
            position = textnode.parse(text, position, end)
    return position

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
            guarded_search(Section.equation_line_pattern, text, position, block_end)
        if equation_line_match:
            assert isinstance(parent, (Document, Section))
            # Current block is a heading, so do a look-ahead to get the nesting
            # level
            if Section.get_nesting_level(text, position) > parent.nesting_level:
                section = Section(parent)
                position = section.parse(text, position, equation_line_match.span())
            else:
                return position
        else:
            # Ordinary paragraph
            paragraph = Paragraph(parent)
            position = paragraph.parse(text, position, block_end)
            position = next_block_start
    return position

class Heading(Node):
    """Class for section headings.  It is the very first child of a `Section`."""
    def __init__(self, parent):
        super(Heading, self).__init__(parent)
    def parse(self, text, position, end):
        position = parse_inline(self, text, position, end)
        return position


class Section(Node):
    """Class for dection, i.e. parts, chapters, sections, subsection etc.

    :cvar equation_line_pattern: regexp for section heading marker lines
    :cvar section_number_pattern: regexp for section numbers like ``#.#``
    :ivar nesting_level: the nesting level of the section. -1 for parts, 0 for
      chapters, 1 for sections etc.  Thus, it is like LaTeX's secnumdepth.

    :type equation_line_pattern: re.pattern
    :type section_number_pattern: re.pattern
    :type nesting_level: int
    """
    equation_line_pattern = re.compile(r"\n[ \t]*={4,}[ \t]*$", re.MULTILINE)
    section_number_pattern = re.compile(r"[ \t]*(?P<numbers>((\d+|#)\.)*(\d+|#))(\.|[ \t\n])[ \t]*",
                                        re.MULTILINE)
    def __init__(self, parent):
        super(Section, self).__init__(parent)
    def parse(self, text, position, equation_line_span):
        section_number_match, self.nesting_level = self.parse_section_number(text, position)
        position = section_number_match.end()
        heading = Heading(self)
        position = heading.parse(text, position, equation_line_span[0])
        position = equation_line_span[1]
        position = parse_blocks(self, text, position)
        return position
    # Class methods because these helpers may also be interesting outside this
    # class
    @classmethod
    def parse_section_number(cls, text, position):
        """Parse the section number and return both the match object and the
        detected nesting level.

        :Parameters:
          - `text`: the source code
          - `position`: the starting position of the heading in the source

        :type text: `preprocessor.Excerpt`
        :type position: int

        :Return:
          - the re.match object of the section number
          - nesting level of the heading, see `nesting_level`

        :rtype: re.match, int
        """
        section_number_match = guarded_match(cls.section_number_pattern, text, position)
        return section_number_match, section_number_match.group("numbers").count(".")
    @classmethod
    def get_nesting_level(cls, text, position):
        """Return the nesting level of the heading at the current parse
        position.

        :Parameters:
          - `text`: the source code
          - `position`: the starting position of the heading in the source

        :type text: `preprocessor.Excerpt`
        :type position: int

        :Return:
          nesting level of the heading, see `nesting_level`

        :rtype: int
        """
        __, nesting_level = cls.parse_section_number(text, position)
        return nesting_level

class Paragraph(Node):
    """Class for single paragraphs of text."""
    def __init__(self, parent):
        super(Paragraph, self).__init__(parent)
    def parse(self, text, position, end):
        return parse_inline(self, text, position, end)

class Emphasize(Node):
    r"""Class for emphasised inline material, like LaTeX's ``\emph``."""
    def __init__(self, parent):
        super(Emphasize, self).__init__(parent)
    def parse(self, text, position, end):
        end_of_emphasize = guarded_find("_", text, position, end)
        position = parse_inline(self, text, position, end_of_emphasize)
        return end_of_emphasize + 1

import copy, inspect
_globals = copy.copy(globals())
Document.node_types = dict([(cls.__name__.lower(), cls) for cls in _globals.values()
                            if inspect.isclass(cls) and issubclass(cls, Node)])
del _globals, cls
