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

from .common import (guarded_match, guarded_search, guarded_find, Node)
from ..src import common
import re

class Document(Node):
    """The root node of a document.

    There is always exactly one Document node in a Gummi AST, and this is the
    top node.  This is not the only thing which is special about it: It also
    contains variables which are "global" to the whole document.  It also
    contains special methods which are used when the whole AST is finished and
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
    :ivar emit: `emitter.Emitter` object used for generating output.  Only
      `Document` and `Text` need `emit` of all routines in this module.
    :cvar node_types: dict which maps `Node` type names to the actual classes.

    :type parent: weakref to Node
    :type root: weakref to Node
    :type nesting_level: int
    :type languages: set
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
        self.emit = None
    def parse(self, text, position=0):
        super(Document, self).parse(text, position)
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
        settings.settings["theme"] = "Standard"
        backend_module = self.find_backend(settings.settings)
        # Bidirectional code injection.  Only `Document` and `Text` need `emit`
        # of all parser.py routines.
        self.emit = backend_module.emit
        self.emit.set_settings(settings.settings)
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

class Heading(Node):
    """Class for section headings.  It is the very first child of a `Section`."""
    def __init__(self, parent):
        super(Heading, self).__init__(parent)
    def parse(self, text, position, end):
        super(Heading, self).parse(text, position)
        position = parse_inline(self, text, position, end)
        return position


class Section(Node):
    """Class for dection, i.e. parts, chapters, sections, subsection etc.

    :cvar equation_line_pattern: regexp for section heading marker lines
    :cvar section_number_pattern: regexp for section numbers like ``#.#``
    :ivar nesting_level: the nesting level of the section.  -1 for parts, 0 for
      chapters, 1 for sections etc.  Thus, it is like LaTeX's secnumdepth.

    :type equation_line_pattern: re.pattern
    :type section_number_pattern: re.pattern
    :type nesting_level: int
    """
    equation_line_pattern = re.compile(r"\n[ \t]*={4,}[ \t]*$", re.MULTILINE)
    section_number_pattern = re.compile(r"[ \t]*(?P<numbers>((\d+|#)\.)*(\d+|#))(\.|[ \t\n])[ \t]*",
                                        re.MULTILINE)
    characteristic_attributes = [common.AttributeDescriptor("nesting_level", "level")]
    def __init__(self, parent):
        super(Section, self).__init__(parent)
    def parse(self, text, position, equation_line_span):
        super(Section, self).parse(text, position)
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
