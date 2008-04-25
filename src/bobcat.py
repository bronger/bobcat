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

"""Currently, this is the main program.  You can test it with::

    python bobcat.py test1.bcat

The result should be test1.tex."""

import sys
from bobcatlib import common, settings, i18n
from bobcatlib.common import FileError
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
                         help=_(u"Name of the log file.  Default: bobcat.log"),
                         default="bobcat.log", metavar=_(u"NAME"))
option_parser.add_option("--nolog", action="store_false", dest="logging",
                         help=_(u"Switch off logging."), default=True)
options, filenames = option_parser.parse_args()

if options.version:
    print u"Bobcat 1.0.  Copyright © 2007 Torsten Bronger, bronger@physik.rwth-aachen.de"
    sys.exit()

if 'epydoc' in sys.modules:
    filenames = ["tests/test1.bcat"]
if len(filenames) != 1:
    print u"Please specify exactly one input file."
    sys.exit()
else:
    settings.settings["input filename"] = filenames[0]
if options.output_file:
    settings.settings["output path"] = options.output_file
settings.settings["backend"] = options.backend

common.setup_logging(options.logfile, options.logging)


from bobcatlib import preprocessor, helpers, parser

text, encoding, bobcat_version = preprocessor.load_file(settings.settings["input filename"])
if bobcat_version != "1.0":
    raise FileError("Bobcat version must be 1.0", settings.settings["input filename"])

document = parser.Document()
document.parse(text)
#helpers.visualize_tree(document.tree_list(), "bobcat.eps")
#helpers.print_tree(document.tree_list())
document.generate_output()

if 'epydoc' in sys.modules:
    import bobcatlib.latex_substitutions
    bobcatlib.latex_substitutions.Substitution.packages = set()
