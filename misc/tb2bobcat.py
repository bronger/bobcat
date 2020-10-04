#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import re, codecs

text_replacements = {}
math_replacements = {}

line_pattern = re.compile(r'0x(?P<hex>[0-9a-f]+)\t[-a-zA-Z0-9]+ +"(?P<replacement>.*)"\Z')
math_pattern = re.compile(r"\$(.+)\${}")
text_math_pattern = re.compile(r"\\ifmmode(?P<math>.+)\\else(?P<text>.+)\\fi{}")
for line in file("/home/bronger/xml/tbook/tbents.txt"):
    if line.strip() == "" or line.startswith("#"):
        continue
    match = line_pattern.match(line.rstrip())
    character = unichr(int(match.group("hex"), 16))
    replacement = match.group("replacement")
    math_match = math_pattern.match(replacement)
    text_math_match = text_math_pattern.match(replacement)
    if math_match:
        math_replacements[character] = math_match.group(1)
    elif text_math_match:
        math_replacements[character] = text_math_match.group("math").strip()
        c = text_math_match.group("text").strip()
        if c[-1] != "}":
            c += "\\"
        text_replacements[character] = c
    else:
        if replacement[-2:] == "{}":
            replacement = replacement[:-2] + "\\"
        text_replacements[character] = replacement.strip()

outfile = codecs.open("en.bls", "w", encoding="utf-8")

print>>outfile,u""".. -*- mode: text; language-code: en -*-
.. Bobcat LaTeX substitutions

.. Es gibt folgende Modi: TEXT, MATH, SECTION, INDEX, BIBTEX
.. 
.. Sprachen werden nach RFC 4646 angegeben.  In den „Modus-Zeilen“ werden die
.. einzelnen Items mit Whitespace oder Kommas getrennt (Kommas werden wie ein
.. Leerzeichen behandelt).  Es *muß* auf jeden Fall genau ein Modus angegeben
.. werden, und zwar ganz am Anfang.  Sprachen sind optional.  Wird keine
.. Sprache angegeben, wird die Dateisprache angenommen.  Die Angaben in der
.. Modus-Zeile sind nicht akkumulierend, d.h. sie *ersetzen* Angaben in
.. vorangehenden Modus-Zeilen vollständig.

"""

print>>outfile, u"TEXT"
last_value = 0
for c in sorted(text_replacements):
    if ord(c) - last_value > 1:
        print>>outfile
    if ord(c) - last_value > 10:
        print>>outfile
    last_value = ord(c)
    if c.isspace():
        print>>outfile, u"0x%x" % ord(c) + "\t\t" + text_replacements[c]
    else:
        print>>outfile, c + "\t\t" + text_replacements[c]

print>>outfile, u"""

.. ........................................................
.. ........................................................
"""
print>>outfile, u"MATH"
last_value = 0
for c in sorted(math_replacements):
    if ord(c) - last_value > 1:
        print>>outfile
    if ord(c) - last_value > 10:
        print>>outfile
    last_value = ord(c)
    if c.isspace():
        print>>outfile, u"0x%x" % ord(c) + "\t\t" + math_replacements[c]
    else:
        print>>outfile, c + "\t\t" + math_replacements[c]
