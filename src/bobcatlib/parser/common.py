#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2008 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Bobcat program.
#
#    Bobcat is free software; you can use it, redistribute it and/or modify it
#    under the terms of the MIT license.
#
#    You should have received a copy of the MIT license with Bobcat.  If not,
#    see <http://bobcat.origo.ethz.ch/wiki/Licence>.
#

__all__ = ["guarded_match", "guarded_search", "guarded_find", "Node"]

import weakref
from ..bobcatlib import common

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
    u"""Abstract base class for all elements in the AST.  It will never be
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

    :ivar characteristic_attributes: Attributes of this class that are
      considered important enough so that they are printed for debugging
      purposes.  This is the nesting depth of sections for example.  The
      entries are either attribute names or 2-tuples with the first element
      being the name of the attribute and the second a “human” name for it.

    :ivar types_path: path containing all ancestor element types in proper
      order.  For example, it may be ``"/Document/Paragraph/Emphasize/Text"``.

    :ivar __original_text: The original text from which this node was created
      (parsed). Only needed for calculating `__position`, see the `position`
      property.
    :ivar __start_index: The index within `__original_text` where this node
      starts.  Only needed for calculating `__position`, see the `position`
      property.
    :ivar __position: cache for the original position of this node in the
      source file, see the `position` property.
    :ivar __text: cache for the text equivalent of this node in the source
      file, see the `text` property.

    :type parent: weakref to Node
    :type root: weakref to Node
    :type children: list of Nodes
    :type language: str
    :type characteristic_attributes: list `common.AttributeDescriptor`
    :type types_path: str
    :type __original_text: `prepocessor.Excerpt`
    :type __start_index: int
    :type __position: `common.PositionMarker`
    :type __text: unicode
    """
    __position = None
    characteristic_attributes = []
    __text = None
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
            self.types_path = parent.types_path + "/" + str(self.__class__).split(".")[1][:-2]
        else:
            # This is the root node
            self.parent = None
            self.language = None
            self.types_path = ""
        self.children = []
    def parse(self, text, position):
        u"""Parse a part of the source document and interpret it as the source
        representation of the current node.  Construct the current node and in
        particular its children according to that representation.

        This is some sort of second ``__init__`` method.  In particular, its
        signature differs from class to class.  However, doing it here rather
        than in the official constructor gives more flexibility to the result
        values.  Additionally, it makes the source more legible.

        Derived classes must call this parse method at the beginning of their
        parse method.  They may safely throw away the result value.

        :Parameters:
          - `text`: source document
          - `position`: starting position of the parsing

        :type text: `preprocessor.Excerpt`
        :type position: int

        :Return:
          The new position in the source document, i.e. the starting position
          of the following document part.  For example, for an emphasise node
          which is enclosed in underscores ``_…_``, it is the very next
          character position after the second underscore.

        :rtype: int
        """
        # pylint: disable-msg=R0201,W0613
        self.__original_text, self.__start_index = text, position
        return position
    def __get_position(self):
        """Returns the starting position of this element.  In some situations,
        for example when a parse error must be reported, it is necessary to
        have the position of the element in the original source files.
        However, calculating the position is rather costly and should only be
        done if it is really needed.

        Therefore, the position is calculated in this private method and cached
        in ``self.__position``.  To get this working, it is necessary that the
        ``parse`` method stored the original text and starting position in two
        private instance variables that are used here for the calculation.

        :Return:
          the original position in the source file

        :rtype: `common.PositionMarker`
        """
        if not self.__position:
            self.__position = self.__original_text.original_position(self.__start_index)
        return self.__position
    position = property(__get_position, doc="""Starting position of this
        document element in the original source file.

        :type: `common.PositionMarker`""")
    def __get_text(self):
        if not self.__text:
            self.__text = u"".join(child.text for child in self.children)
        return self.__text
    text = property(__get_text, doc="""Text of this node and all of its
        children.  This is very similar to the ``text()`` function in XPath.
        Note that it is overwritten with an ordinary attribute in the `Text`
        class.

        *Important*: You must not read this property while the element is
        parsed.  The reason is simply that then the caching will lead to
        incorrect results in future calls.

        :type: unicode""")
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
          A (nested) list of nodes to be used in `helpers.print_tree`.

        :rtype: list
        """
        if self.children:
            return [self, [child.tree_list() for child in self.children]]
        else:
            return self
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
    def throw_parse_error(self, description, position_marker=None):
        """Adds a parsing error to the list of parsing errors.

        :Parameters:
          - `description`: description of what went wrong
          - `position_marker`: the position where the error happened.  If not
            given, the starting point of this element is used.

        :type description: unicode
        :type position_marker: `common.PositionMarker`
        """
        common.add_parse_error(
            common.ParseError(self, description, position_marker=position_marker))
    def throw_parse_warning(self, description, position_marker=None):
        """Adds a parsing warning to the list of parsing errors.

        :Parameters:
          - `description`: description of what was sub-optimal
          - `position_marker`: the position where the warning happened.  If not
            given, the starting point of this element is used.

        :type description: unicode
        :type position_marker: `common.PositionMarker`
        """
        common.add_parse_error(
            common.ParseError(self, description, "warning", position_marker))
