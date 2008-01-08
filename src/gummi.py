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

"""Currently, this is the main program.  You can test it with::

    python gummi.py test1.rsl

The result should be test1.tex."""

import os, sys, common, i18n
_ = i18n.ugettext

import optparse
option_parser = optparse.OptionParser("usage: %prog [options] filename")
option_parser.add_option("--version", action="store_true", dest="version",
                         help=_(u"Print out version number and copying information"),
                         default=False)
option_parser.add_option("--config", type="string",
                         dest="config_file",
                         help=_(u"Name of the config file."),
                         default=None, metavar=_(u"FILENAME"))
option_parser.add_option("-o", "--output", type="string",
                         dest="output_file",
                         help=_(u"Name of the output file."),
                         default=None, metavar=_(u"FILENAME"))
option_parser.add_option("-b", "--backend", type="string",
                         dest="backend",
                         help=_(u"Name of the backend.  Default: latex"),
                         default="latex", metavar=_(u"NAME"))
option_parser.add_option("-l", "--logfile", type="string",
                         dest="logfile",
                         help=_(u"Name of the log file.  Default: gummi.log"),
                         default="gummi.log", metavar=_(u"NAME"))
option_parser.add_option("--nolog", action="store_false", dest="logging",
                         help=_(u"Switch off logging."), default=True)
options, filenames = option_parser.parse_args()

if options.version:
    print u"Gummi 1.0.  Copyright © 2007 Torsten Bronger, bronger@physik.rwth-aachen.de"
    sys.exit()

if 'epydoc' in sys.modules:
    filenames = ["misc/test1.rsl"]
if len(filenames) != 1:
    print u"Please specify exactly one input file."
    sys.exit()
else:
    common.settings["input filename"] = filenames[0]
if options.output_file:
    common.settings["output path"] = options.output_file
common.settings["backend"] = options.backend

common.setup_logging(options.logfile, options.logging)


import preprocessor, helpers
parser = helpers.import_local_module("parser")

text, encoding, gummi_version = preprocessor.load_file(common.settings["input filename"])
if gummi_version != "1.0":
    raise FileError("Gummi version must be 1.0", common.settings["input filename"])

document = parser.Document()
document.parse(text)
#print [document.tree_list()]
#print helpers.print_tree([document.tree_list()])
document.generate_output()

if 'epydoc' in sys.modules:
    import latex_substitutions
    latex_substitutions.Substitution.packages = set()
