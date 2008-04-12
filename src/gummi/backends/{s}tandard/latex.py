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

"""The LaTeX backend for the Standard theme.

:var emit: The emitter for this backend.

:var packages: additional LaTeX packages needed by this document, especially
  due to occurences of exotic Unicode characters.

:var babel_options: Mapping from :RFC:`4646` language codes to options for
  LaTeX's babel package.

:type emit: `emitter.Emitter`
:type packages: set of str
:type babel_options: dict
"""

import os.path, codecs
from gummi import emitter, latex_substitutions

class Emitter(emitter.Emitter):
    def do_final_processing(self):
        """So far, only the LaTeX file is generated."""
        if self.settings["output path"]:
            output_filename = self.settings["output path"]
        elif self.settings["input filename"]:
            output_filename = os.path.splitext(self.settings["input filename"])[0] + ".tex"
        else:
            output_filename = "out.tex"
        if output_filename == self.settings["input filename"]:
            output_filename = output_filename[:-4] + "_1.tex"
        outfile = codecs.open(output_filename, "w", "latin-1")
        self.output = self.output.replace("\n\n\\par ", "\n\n")
        outfile.write(self.output)
        outfile.close()

emit = Emitter()

packages = set()

nesting_level_offset = 2   # We're making an article; for a book, it'd be 1
babel_options = {"af": "afrikaans",
                 "new": "bahasa", "nwc": "bahasa",
                 "eu": "basque",
                 "br": "breton",
                 "chu": "bulgarian", "bg": "bulgarian", "cu": "bulgarian",
                 "ca": "catalan",
                 "hr": "croatian",
                 "cs": "czech",
                 "da": "danish",
                 "dum": "dutch", "nl": "dutch",
                 "ang": "english", "enm": "english", "en": "english",
                 "en-us": "USenglish", "en-gb": "UKenglish", "en-ca": "canadian",
                 "en-au": "australian", "en-nz": "newzealand",
                 "eo": "esperanto",
                 "et": "estonian",
                 "fi": "finnish",
                 "fr": "french", "fr-ca": "canadien",
                 "gl": "galician",
                 "de": "ngerman", "de-de": "ngerman", "de-de-1901": "german", "de-1901": "german",
                 "de-at": "naustrian", "de-at-1901": "austrian",
                 "el": "greek",
                 "he": "hebrew",
                 "hu": "hungarian",
                 "is": "icelandic",
                 "ia": "interlingua",
                 "ga": "irish",
                 "it": "italian",
                 "la": "latin",
                 "dsb": "lowersorbian", "wen": "uppersorbian", "hsb": "uppersorbian",
                 "sme": "samin", "sma": "samin", "smi": "samin", "smj": "samin", "smn": "samin", "sms": "samin",
                 "no": "nynorsk", "nb": "norsk", "nn": "nynorsk",
                 "pl": "polish",
                 "pt": "portuguese", "pt-br": "brazilian",
                 "ro": "romanian",
                 "ru": "russian",
                 "gd": "scottish",
                 "es": "spanish",
                 "sk": "slovak",
                 "sl": "slovene",
                 "sv": "swedish",
                 "sr": "serbian",
                 "tr": "turkish", "ota": "turkish", "crh": "turkish",
                 "uk": "ukrainian",
                 "cy": "welsh"}

def find_babel_option(language):
    """Finds the base babel option for a given :RFC:`4646` language code.

    :Parameters:
      - `language`: language as :RFC:`4646` language code

    :type language: str
    
    :Return:
      The best Babel option for `language`.  If all else fails, it's
      ``english``.

    :rtype: str
    """
    language = language.lower()
    if language in babel_options:
        return babel_options[language]
    else:
        parts = language.split("-", 2)
        if parts[0] + "-" + parts[1] in babel_options:
            return babel_options[parts[0] + "-" + parts[1]]
        elif parts[0] in babel_options:
            return babel_options[parts[0]]
        else:
            return "english"

def process_document(self):
    """Emit the document structure.  So far, we only do articles."""
    emit(r"""\documentclass{article}

\usepackage[latin1]{inputenc}
\usepackage[T1]{fontenc}
""")
    minor_babel_options = set([find_babel_option(language) for language in self.languages])
    main_babel_option = find_babel_option(self.language)
    minor_babel_options.remove(main_babel_option)
    babel_options = list(minor_babel_options) + [main_babel_option]
    emit(u"\\usepackage[%s]{babel}\n" % ", ".join(babel_options))
    preamble = emit.pop_output()
    emit("\\usepackage{hyperref}\n")
    emit("\n\\begin{document}\n\n")
    self.process_children()
    emit("\\end{document}\n")
    body = emit.pop_output()
    # Now we do the emitting again, this time with the additional packages
    emit(preamble)
    if packages:
        emit("\\usepackage{%s}\n" % ", ".join(packages))
    emit(body)

def process_paragraph(self):
    """Emit a single paragraph."""
    emit(r"\par ")
    self.process_children()
    emit("\n\n")

def process_section(self):
    """Emit a section of arbitrary nesting depth, and its heading.  (So, a
    special routine for heading is not necessary.)"""
    section_name = ["part", "chapter", "section", "subsection", "subsubsection",
                    "paragraph", "subparagraph"][self.nesting_level+nesting_level_offset]
    emit(r"\%s{" % section_name)
    self.children[0].process()
    emit("}\n\n")
    for child in self.children[1:]:
        child.process()

def process_emphasize(self):
    """Emit emphasized text."""
    emit(r"\emph{")
    self.process_children()
    emit("}")

def process_hyperlink(self):
    """Emit a hyperlink."""
    emit(r"\url{%s}" % self.url)

def process_text(self):
    """Emit an ordinary text node.  I have to override the default because Unicodes
    must be transformed into LaTeX macros.

    It also collects all needed packages."""
    emit(latex_substitutions.process_text(self.text, self.language, "TEXT", packages))
