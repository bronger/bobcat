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

class Label(object):
    """Labels that are given to elements of a document.  A sequence of labels
    form a path to an element.  Note that (incomplete) paths given by the user
    to point to another part of the document don't consist of Labels but of
    strings (or rather, regular expressions).
    """
    def __init__(self, labels, is_section=True, is_include=False):
        """
        :Parameters:
          - `labels`: sequence of label names, all associated with the same
            element.  Mostly, its length is one or two, depending on whether an
            explicit label was given, too.  (The other one which is given
            always is the implicit label.)
          - `is_section`: denotes whether this label belongs to a sectioning
            element
          - `is_include`: denotes whether this label belongs to a document
            element which was inserted into the main document.

        :type labels: list or tuple of unicode
        :type is_section: bool
        :type is_include: bool
        """
        assert isinstance(labels, (list, tuple))
        normalized_labels = set()
        for label in labels:
            normalized_labels.add(u" ".join(label.split())[:80])
        self.__labels = frozenset(normalized_labels)
        self.__is_include = is_include
        self.__is_section = is_section
    def __contains__(self, item):
        """
        :Parameters:
          - `item`: the regular expression that represents the requested
            label.

        :type item: re.pattern

        :Return:
          whether `item` matches one of the alternative names of this label

        :rtype: bool
        """
        for label in self.__labels:
            if item.match(label):
                return True
        return False
    def __eq__(self, other):
        return self.__labels == other.__labels
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        """Note that labels that only differ in `is_section` or `is_include`
        are not considered different because the author cannot distinguish
        between them, so it must be regarded as a label clash."""
        return hash(self.__labels)
    is_section = property(lambda self: self.__is_section,
                          doc="""whether this label belongs to a sectioning
    element.

    :type: bool
    """)
    is_include = property(lambda self: self.__is_include,
                          doc="""whether this label belongs to a document
    element which was inserted into the main document.

    :type: bool
    """)

class LabelLookupError(common.Error):
    """Error for missing or ambiguous labels.

    :ivar label: the label which caused the error

    :type label: `preprocessor.Excerpt`
    """
    def __init__(self, description, label):
        super(LabelLookupError, self).__init__(description)
        self.label = label

class LabelNotFoundError(LabelLookupError):
    """This is raised if no fitting label was found at all during a
    cross-reference lookup.
    """
    def __init__(self, description, label):
        super(LabelNotFoundError, self).__init__(description, label)

class LabelPathAmbiguousError(LabelLookupError):
    """This is raised if there are two paths that could have been meant with a
    label lookup.  The difference to the `LabelAmbiguousError` is that here,
    the ambiguity can be solved by changing (mostly expanding) the path used in
    the cross reference.  In case of a `LabelAmbiguousError` however, you have
    to change labels in order to make them resolvable.

    :ivar possible_paths: all paths that could have been meant by the lookup.

    :type possible_paths: set of tuple of `Label`
    """
    def __init__(self, description, label, possible_paths):
        super(LabelPathAmbiguousError, self).__init__(description, label)
        self.possible_paths = possible_paths

class LabelAmbiguousError(LabelLookupError):
    """This is raised if two elements could be meant with a cross-reference
    lookup because they share exactly the same absolute label path.  The only
    remedy is to change one of their labels.

    :ivar elements: the elements that could be meant

    :type elements: set of `Node`
    """
    def __init__(self, description, label, elements):
        super(LabelAmbiguousError, self).__init__(description, label)
        self.elements = elements

class CrossReferencesDict(object):
    """Dictionary mapping labels to AST elements.  It is supposed to be used
    for labels from the Big Namespace (sections, captions, environments, and
    formulae).  Normally, the keys are of type `Label`, but they may be tuples
    of such, containing also the labels of the parent sections: ``("Section",
    "Subsection")``.

    The values are normally elements of the AST.  If case of ambiguities, they
    are sets of those.  Eventually, this will lead to errors if such a label is
    really used in the document but for a proper error message all elements
    with that label must be known, so they are collected here.

    :ivar elements_by_labelpath: maps absolute label paths to document
      elements.  If the mapping is not unique, it maps to a set of elements.

    :type elements_by_labelpath: dict mapping tuple to `Node`
    """
    elements_by_labelpath = {}
    def register(self, label_path, value):
        """Register one referencable AST element with the dictionary.

        Note that the label_path is a tuple.  The reason for this is the
        following: In order to avoid ambiguities, the user may give a reference
        with an arrow: "``Measurements → Results``".  This points to the
        section "Results" in the parent section/chapter "Measurements".  This
        is represented as the tuple ``("Measurements", "Results")`` (of course
        with `Label`'s rather than ``string``'s).

        :Parameters:
          - `label_path`: The *absolute* label path that should be added to the
            dict.
          - `value`: the node to which the label belongs

        :type label_path: tuple of `Label`
        :type value: Node
        
        """
        assert isinstance(label_path, tuple)
        assert isinstance(value, Node)
        if label_path in elements_by_labelpath:
            if isinstance(elements_by_labelpath[label_path], set):
                elements_by_labelpath[label_path].add(value)
            else:
                # I create a set because one element can have two labels which
                # would be totally okay and unambiguous.  Labels to elements
                # needn't be injective.  Instead, there may be an explicit and
                # and implicit label.
                elements_by_labelpath[label_path] = set([elements_by_labelpath[label_path], value])
        else:
            elements_by_labelpath[label_path] = value
        for label in label_path[-1]:
            if label in paths_by_last_label:
                paths_by_last_label[label].add(label_path)
            else:
                paths_by_last_label[label] = set([label_path])
    @staticmethod
    def construct_path_tuple(label_path):
        """Parse a label path taken directly from the document and create a
        tuple of regular expressions from it.

        :Parameters:
          - `label_path`: the sparse label path given by the author in the
            document, possibly using the arrow and ellipsis notation.

        :type label_path: `preprocessor.Excerpt`

        :Return:
          a tuple containing the regular expression that can be used to match
          against the known absolute paths

        :rtype: tuple of re.pattern
        """
        assert isinstance(label_path, preprocessor.Excerpt)
        path = []
        for part in label_path.split(u"→"):
            characters = list(unicode(part))
            # FixMe: The current implementation treats all occurances of \u0000
            # as ellipses, too.
            for position in (i.start() for i in re.finditer(u"…", part.escaped_text())):
                characters[position] = u"\u0000"
            part = u"".join(characters)
            # Note that sparse paths are not truncated after 80 characters
            # because they won't clutter up memory because they are always
            # explicitly given.
            part = u" ".join(part.split())
            i = 0
            part_with_wildcards = u""
            while i < len(part):
                j = part.find(u"\u0000", i)
                if j == -1:
                    part_with_wildcards += part[i:]
                    break
                else:
                    part_with_wildcards += part[i:j] + u".+"
                    i = j
            path.append[re.compile(part_with_wildcards + u"$", re.UNICODE)]
        return tuple(path)
    @staticmethod
    def path_in_current_document(path):
        """Test whether the given path lies completely in the main document or
        not.

        :Parameters:
          - `path`: an absolte label path

        :type path: tuple of `Label`

        :Return:
          ``True`` if `path` points to an element in the main document, or
          ``False`` if it points to an element of a child document

        :rtype: bool
        """
        for label in path:
            if label.is_include:
                return False
        return True
    def extract_element(self, found_path, original_label_path):
        """Returns the finally found element.  The reason why this is
        encapsulated into a function is that the possible error situation of
        two label paths pointing to the same element must be handled.

        :Parameters:
          - `found_path`: absolute label path that was found during the lookup
            process
          - `original_label_path`: The document source code snippet with the
            path the author gave.  This is only used for generating an error
            message if necessary.

        :type found_path: tuple of `Label`
        :type original_label_path: preprocessor.Excerpt

        :Return:
          the element to which `found_path` points

        :rtype: Node
        """
        element = self.elements_by_labelpath[found_path]
        if isinstance(element, set):
            raise LabelAmbiguousError(u"very same label was given multiple times",
                                      original_label_path, element)
        return element
    def lookup(self, label_path, current_label_path):
        """Returns the element that the given label path points to.
        
        :Parameters:
          - `label_path`: The relative or absolute or sparse label path that
            should be looked up.
          - `current_label_path`: the absolute path of the element which
            requests the lookup.

        :type label_path: `preprocessor.Excerpt`
        :type current_label_path: tuple of `Label`
        
        :Return:
          The AST element the label is pointing to.

        :rtype: `Node`

        :Exceptions:
          - `LabelNotFoundError`: raised if the label was not found at all.
          - `LabelPathAmbiguousError`: raised if there are two label paths that
            could be meant by the given key.
          - `LabelAmbiguousError`: raised if two elements share exactly the
            same label (namely the one requested) so that it cannot be
            resolved.
        """
        path_candidates = set()
        reversed_path_tuple = reversed(self.construct_path_tuple(label_path))
        for path in self.elements_by_labelpath:
            i = len(path) - 1
            for regular_expression in reversed_path_tuple:
                if i < 0:
                    break
                if regular_expression in path[i]:
                    i -= 1
                    continue
                else:
                    i -= 1
            else:
                path_candidates.add(path)
        if not path_candidates:
            raise LabelNotFoundError(u"label was not found", label_path)
        elif len(path_candidates) == 1:
            return self.extract_element(path_candidates[0], label_path)
        else:
            # Okay, there was more than one path that fitted.  We try to reduce
            # the set by giving higher priority to paths in the same section
            # and the same document.
            #
            # First, prune the current label path to the deepest section
            while current_label_path and not current_label_path[-1].is_section:
                current_label_path = current_label_path[:-1]
            paths_in_current_section = [path for path in path_candidates
                                        if path[:-1] == current_label_path]
            if len(paths_in_current_section) == 1:
                return self.extract_element(paths_in_current_section[0], label_path)
            elif len(paths_in_current_section) > 1:
                raise LabelPathAmbiguousError(u"more than one label path in the local "
                                              u"section is possible",
                                              label_path, paths_in_current_section)
            else:
                # Since no path candidate was found in the current section, we
                # make a second try to narrow the list of possible candidates
                # by taking out all that are in child documents.
                paths_in_current_document = [path for path in path_candidates
                                             if self.path_in_current_document(path)]
                if len(paths_in_current_document) == 1:
                    return self.extract_element(paths_in_current_document[0], label_path)
                else:
                    raise LabelPathAmbiguousError(u"more than one label path is possible",
                                                  label_path, path_candidates)

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

        This is some sort of second ``__init__`` method.  In particular, its
        signature differs from class to class.  However, doing it here rather
        than in the official constructor gives more flexibility to the result
        values.  Additionally, it makes the source more legible.

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
        position = parse_inline(self, text, position, end)
        assert text[position] == "_"
        return position + 1

class Hyperlink(Node):
    """Class for hyperlinks aka weblinks.

    :ivar url: the URL of this hyperlink

    :type url: unicode
    """
    def __init__(self, parent):
        super(Hyperlink, self).__init__(parent)
    def parse(self, text, position, end):
        if text[position] == "<" and text[end-1] == ">":
            self.url = unicode(text)[position+1:end-1]
        else:
            raise NotImplementedError("Only URL-only hyperlinks are implemented so far")
        return end

import copy, inspect
_globals = copy.copy(globals())
Document.node_types = dict([(cls.__name__.lower(), cls) for cls in _globals.values()
                            if inspect.isclass(cls) and issubclass(cls, Node)])
del _globals, cls

if __name__ == "__main__":
    import doctest
    doctest.testmod()
