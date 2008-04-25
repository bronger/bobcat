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
    file).  Then, generating the output is more than just concatenating
    `self.output`.

    The emitter is instantiated in the backend module.  The parser module
    copies this into the `parser.Document` object and passes the settings
    to it through `set_settings`.  Then, the actual processing is done on the
    AST, during which the `__call__` method is invoked very often with the
    generated output text (in the correct order).  Finally, the
    `bobcatlib.parser.sectioning.Document` object in parser.py calls
    `do_final_processing`.  This method must be overridden in the derived class
    in the backend!  It can write self.output to a file for example or more.

    :ivar output: serialised output of the current document processing.
    :ivar settings: settings for the emitter like name of the input file and
      further generation details (e.g. whether HTML sing file/multiple file).

    :type output: unicode
    :type settings: dict
    """
    def __init__(self):
        """Class constructor."""
        self.output = u""
        self.settings = None
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
        `parser.sectioning.Document.generate_output` method in the
        `sectioning.Document` root node.

        The method is not defined in this abstract base class, so it must be
        overridden in the derived class in the backend.  You may use
        `self.settings` in this method."""
        raise NotImplementedError
