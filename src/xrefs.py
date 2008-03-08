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
"""Management of cross references of various kinds in Gummi documents.

This module defines the classes and exceptions necessary for cross references
management in Gummi documents.  This covers the actual cross references to
sections or figures as well as bibliographical citations, text blocks,
footnotes, and so-called delayed weblinks.

Note that nothing is parsed here.  This module just resolves the references and
makes the connection between referencing document element and referred element.
"""

import common

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

class ReferencingNode(object):
    """An abstract base class for AST elements that want to refer to other AST
    elements.  This is intended to be for cross references, citations, and text
    blocks.  Note that ``ReferencingNode`` is not derived from `parser.Node`.
    So such element classes must have *two* parents, `parser.Node` and
    ``ReferencingNode`` (in this order).

    Actually, the only purpose of this class is to make clear that elements
    that want to use CrossReferencesManager must have a method called
    `resolve_cross_references`.
    """
    def resolve_cross_references(self, cross_references_manager):
        """This method is called by `CrossReferencesManager.close()` if the
        element has registered itself for callback.  Usually, it will call
        ``cross_references_manager.lookup`` here for finding the element(s) it
        is refering to.

        In this method, all errors must be handled, too, for example if a label
        path could not be found.

        :Parameters:
          - `cross_references_manager`: the cross references manager that is
            responsible for the element's cross referencing, i.e. for ordinary
            cross references, citations, or text blocks.

        :type cross_references_manager: `CrossReferencesManager`
        """
        raise NotImplementedError

class ReferencesManager(object):
    """Abstact base class for all classes that manage cross references.  This
    includes all types of cross references managers: ordinary cross references,
    citations, text blocks, but also footnotes and delayed weblinks.
    """
    def close(self):
        """Called when the document is completely parsed.  It ensures that all
        references have been resolved, and errors have been properly handled.

        After this method was called, the references manager is in an undefined
        state and cannot be used for further lookups anymore.
        """
        raise NotImplementedError

class CrossReferencesManager(ReferencesManager):
    """References manager mapping label paths to AST elements.  It is supposed
    to be used for labels from the Big Namespace (sections, captions,
    environments, and formulae) as well as citations and text blocks.

    The values are elements of the AST.  If case of ambiguities, they are sets
    of those.  Eventually, this will lead to errors if such a label is really
    used in the document but for a proper error message all elements with that
    label must be known, so they are collected here.

    :ivar elements_by_labelpath: maps absolute label paths to document
      elements.  If the mapping is not unique, it maps to a set of elements.
    :ivar requesters: all document elements that want to be called back when
      this CrossReferencesManager is finished.

    :type elements_by_labelpath: dict mapping tuple to `Node`
    :type requesters: set of `ReferencingNode`
    """
    elements_by_labelpath = {}
    requesters = set()
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
            # as ellipses, too.  This means that there must not be any NULL
            # character in Gummi input source files.
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
        """Internal method that returns the finally found element.  The reason
        why this is encapsulated into a function is that the possible error
        situation of two label paths pointing to the same element must be
        handled.

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
    def register_requester(self, element):
        """Register an AST element for getting a callback when the cross
        references are completely collected so that lookups can be performed.
        See `ReferencingNode` for more information.

        :Parameters:
          - `element`: the element that wants to be called back.

        :type element: ReferencingNode
        """
        assert element not in self.requesters
        self.requesters.add(element)
    def close(self):
        for requester in self.requesters:
            requester.resolve_cross_references(self)
        self.elements_by_labelpath.clear()
        self.requesters.clear()

class MarkBasedNode(object):
    """Abstract common base class for footnotes and delayed weblinks.  Note
    that ``MarkBasedNode`` is not derived from `parser.Node`.  So such element
    classes must have *two* parents, `parser.Node` and ``MarkBasedNode`` (in
    this order).

    :ivar referenced_element: The element that the current element points to.
      This can be the footnote or the delayed weblink.  It is ``None`` as long
      as the reference has not been resolved yet.

    :type referenced_element: `parser.Node`
    """
    # FixMe: Maybe the label/mark should be made an instance variable, too.
    # Then, it wouldn't be necessary anymore to give it as an explicit
    # parameter everywhere in the classes of this module.  Maybe this class can
    # be given up completely in favour of the main node classes for footnotes
    # and delayed weblinks.
    referenced_element = None
    def handle_resolving_failure(self, label_error):
        """Called by the responsible ``ReferencedManager`` if the reference
        could not be resolved.

        :Parameters:
          - `label_error`: exception with the exact error

        :type label_error: `LabelNotFoundError`
        """
        raise NotImplementedError

class SpuriousFootnoteMarkError(common.Error):
    """Error for odd footnotes that are never used.

    :ivar mark: the footnote mark that was never used
    :ivar footnote: the footnote element that was never used

    :type mark: unicode
    :type footnote: `parser.Footnote`
    """
    def __init__(self, mark, footnote):
        super(SpuriousFootnoteMarkError, self).__init__("no reference to this footnote found")
        self.mark, self.footnote = mark, footnote

class FootnotesManager(ReferencesManager):
    """References manager for footnotes.  Footnotes can register themselves
    here, and Footnote references can do so, too.  The goal is to create a link
    from the reference to the footnote.

    :ivar requesters_by_mark: all requesters waiting to be linked to
      footnotes.  The keys are the footnote marks.  They are mapped to lists of
      the respective requesters.

    :type requesters_by_mark: dict mapping unicode to list of
      `parser.FootnoteReference`
    """
    requesters_by_mark = {}
    def register_requester(self, mark, element):
        """Adds a footnote references to the waiting queue to be linked to its
        footnote.

        :Parameters:
          - `mark`: the footnote mark
          - `element`: the footnote reference that looks for its footnote

        :type mark: unicode
        :type element: `parser.FootnoteReference`
        """
        assert isinstance(element, MarkBasedNode)
        import parser
        assert isinstance(delayed_weblink_reference, parser.FootnoteReference)
        self.requesters_by_mark.get(mark, []).append(element)
        # In these lists, every element must occur only once
        assert sorted(set(self.requesters_by_mark[mark])) == sorted(self.requesters_by_mark[mark])
    def register(self, mark, footnote):
        """Registers a footnote with this manager.  This means that the
        footnote reference that references to this footnote is linked to it.

        :Parameters:
          - `mark`: the footnote mark
          - `footnote`: the footnote element

        :type mark: unicode
        :type footnote: `parser.Footnote`
        """
        try:
            self.requesters_by_mark[mark].pop(0).referenced_element = footnote
        except KeyError, IndexError:
            raise SpuriousFootnoteMarkError(mark, footnote)
    def start_new_section(self):
        """Resets the footnotes manager because a new section was started.
        Remember that footnotes can be referenced only in the current section.
        Therefore, it is necessary to clear everything at the start of a new
        section.  However, before this happens, all footnote references that
        could not be linked to a footnote must be notified.

        :Exceptions:
          - `LabelNotFoundError`: if a footnote reference could not be
            resolved.
        """
        for mark, requester_list in self.requesters_by_mark.iteritems():
            for element in requester_list:
                element.handle_resolving_failure(
                    LabelNotFoundError("no footnote with this mark found", mark))
        self.requesters_by_mark.clear()
    def close(self):
        # Alias for `start_new_section`.
        self.start_new_section()

class DelayedWeblinksManager(ReferencesManager):
    """References manager for delayed weblinks.  It creates links from delayed
    weblinks references to the delayed weblinks themselves.

    :ivar requesters_by_label: all delayed weblinks references.  The keys are
      the labels which are mapped to sets of delayed weblinks references.
    :ivar current_definition_by_label: all currently known labels, mapped to
      their most recent delayed weblinks
    :ivar unserved_requesters: delayed weblinks referenced which havn't yet
      gotten a link to a delayed weblink.

    :type requesters_by_label: dict mapping unicode to set of
      `parser.DelayedWeblinkReference`
    :type current_definition_by_label: dict mapping unicode to
      `parser.DelayedWeblink`
    :type unserved_requesters: set of `parser.DelayedWeblinkReference`
    """
    requesters_by_label = {}
    current_definition_by_label = {}
    unserved_requesters = set()
    def register_requester(self, label, delayed_weblink_reference):
        """Adds a delayed weblink reference to the waiting queue to be linked
        to its delayed weblink.  If there is already a definition for this
        label, it is written to the delayed weblink reference.

        :Parameters:
          - `label`: the whitespace-normalized contents of the delayed
            weblink which serves as a label
          - `delayed_weblink_reference`: the delayed weblink reference itself

        :type label: unicode
        :type delayed_weblink_reference: `parser.DelayedWeblinkReference`
        """
        assert isinstance(delayed_weblink_reference, MarkBasedNode)
        import parser
        assert isinstance(delayed_weblink_reference, parser.DelayedWeblinkReference)
        self.requesters_by_label.get(label, set()).add(delayed_weblink_reference)
        if label in current_definition_by_label:
            delayed_weblink_reference.referenced_element = current_definition_by_label[label]
        else:
            self.unserved_requesters.add(delayed_weblink_reference)
    def register(self, label, delayed_weblink):
        """Registers a delayed weblink with this manager.  This means that all
        dangling delayed weblinks references that uses this label are
        resolved.

        :Parameters:
          - `label`: the whitespace-normalized contents of the delayed
            weblink which serves as a label
          - `delayed_weblink`: the delayed weblink itself

        :type label: unicode
        :type delayed_weblink: `parser.DelayedWeblink`
        """
        current_definition_by_label[label] = delayed_weblink
        requesters = self.requesters_by_label.pop(label, set())
        for requester in requesters:
            requester.referenced_element = delayed_weblink
            self.unserved_requesters.discard(requester)
    def close(self):
        for label, requesters in self.requesters_by_label.iteritems():
            for requester in requesters:
                if requester in unserved_requesters:
                    requester.handle_resolving_failure(
                        LabelNotFoundError("no delayed weblink with this label found", label))
        self.requesters_by_label.clear()
        self.current_definition_by_label.clear()
        self.unserved_requesters.clear()
