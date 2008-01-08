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

"""The emitter is an object which organises output generation.  This module
exports all of its functionality by the class `Emitter`."""

class Emitter(object):
    """Class for output generators.

    The emitter is an object which holds all the output data and organises the
    generation of the final output.  In the simplest case, this is a file.
    Howver, sometimes some post-processing is necessary.  For example, the
    generated LaTeX file must be transformed to a PDF.

    Additionally, some output types may generate a whole bunch of files
    (e.g. HTML, and even more so if you want to have each chapter in its own
    file).  Then, generatin the output is more than just concetanating
    `self.output`.

    The emitter is instantiatied in the backend module.  The parser module
    copies this into the `Document` object and passes the settings to it
    through `set_settings`.  Then, the actual processing is done on the AST,
    during which the `__call__` method is invoked very often with the generated
    output text (in the correct order).  Finally, the `Document` object in
    parser.py calls `do_final_processing`.  This method must be overridden in
    the derived class in the backend!  It can write self.output to a file for
    example or more.

    :ivar output: serialised output of the current document processing.
    :ivar settings: settings for the emitter like name of the input file and
      further generation details (e.g. whether HTML sing file/multiple file).

    :type output: unicode
    :type settings: dict
    """
    def __init__(self):
        """Class contructor."""
        self.output = u""
    def set_settings(self, settings):
        """Setting the settings for the output.  It is possible to set the
        settings by a mere assignment to `Emitter.settings` but this is
        clearer.  This method is called before any `__call__` or
        `do_final_processing` call so that you can use the settings in these
        methods.

        :Parameters:
          - `settings`: the output setting, e.g. the original input filename
            from which the output filename can be derived.

        :type settings: dict
        """
        self.settings = settings
    def __repr__(self):
        return "Emitter()"
    def __call__(self, text):
        """Emit a certain excerpt of text.  You may use `self.settings` in this
        method.

        :Parameters:
          - `text`: the excerpt of text that is supposed to be appended to the
            current output.

        :type text: preprocessor.Excerpt
        """
        self.output += unicode(text)
    def pop_output(self):
        """Returns the output emitted so far and resets the output to the empty
        string.

        :Return:
          the output emitted so far

        :rtype: unicode
        """
        output = self.output
        self.output = u""
        return output
    def do_final_processing(self):
        """This method generates the actual output, i.e. writes to files,
        creates subdirectories, calls post-processing conversion programs,
        prepares all images etc.  It is called from the
        `parser.Document.generate_output` method in the `Document` root node.

        The method is not defined in this abstract base class, so it must be
        overridden in the derived class in the backend.  You may use
        `self.settings` in this method."""
        assert False
