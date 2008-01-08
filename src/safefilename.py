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

"""Codec class for safe filenames.  Safe filenames work on all important
filesystems, i.e., they don't contain special or dangerous characters, and
they don't assume that filenames are treated case-sensitively.

    >>> u"hallo".encode("safefilename")
    'hallo'
    >>> u"Hallo".encode("safefilename")
    '{h}allo'
    >>> u"MIT Thesis".encode("safefilename")
    '{mit}_{t}hesis'
    >>> u"Gesch\\u00e4ftsbrief".encode("safefilename")
    '{g}esch(e4)ftsbrief'

Of course, the mapping works in both directions as expected:

    >>> "{g}esch(e4)ftsbrief".decode("safefilename")
    u'Gesch\\xe4ftsbrief'
    >>> "{mit}_{t}hesis".decode("safefilename")
    u'MIT Thesis'

"""

import codecs

lowercase_letters = "abcdefghijklmnopqrstuvwxyz"
safe_characters = lowercase_letters + "0123456789-+!$%&'@~#.,^"
uppercase_letters = lowercase_letters.upper()

def encode(input, errors='strict'):
    """Convert Unicode strings to safe filenames.

    :Parameters:
      - `input`: the input string to be converted into a safe filename
      - `errors`: the ``errors`` parameter known from standard ``str.encode``
        methods

    :type input: unicode
    :type errors: str

    :Return:
      the safe filename

    :rtype: str
    """
    output = ""
    i = 0
    input_length = len(input)
    while i < input_length:
        c = input[i]
        if c in safe_characters:
            output += str(c)
        elif c == " ":
            output += "_"
        elif c in uppercase_letters:
            output += "{"
            while i < input_length and input[i] in uppercase_letters:
                output += str(input[i]).lower()
                i += 1
            output += "}"
            continue
        else:
            output += "(" + hex(ord(c))[2:] + ")"
        i += 1
    return output, input_length

def handle_problematic_characters(errors, input, start, end, message):
    """Trivial helper routine in case something goes wrong in `decode`.

    :Parameters:
      - `errors`: the ``errors`` parameter known from standard ``str.encode``
        methods.  It is just passed by `decode`.
      - `input`: the input to be converted to Unicode by `decode`
      - `start`: the starting position of the problematic area as an index in
        ``input``
      - `end`: the ending position of the problematic area as an index in
        ``input``.  Note that this obeys to the standard upper-limit notation
        in Python (range() etc).
      - `message`: error message describing the problem

    :type errors: str
    :type input: str
    :type start: int
    :type end: int
    :type message: str
    
    :Return:
      the single character to be inserted into the output string

    :rtype: unicode
    """
    if errors == 'ignore':
        return u""
    elif errors == 'replace':
        return u"?"
    else:
        raise UnicodeDecodeError("safefilename", input, start, end, message)

def decode(input, errors='strict'):
    """Convert safe filenames to Unicode strings.

    :Parameters:
      - `input`: the input string to be converted from a safe filename to an
        ordinary Unicode string
      - `errors`: the ``errors`` parameter known from standard ``str.encode``
        methods

    :type input: str
    :type errors: str

    :Return:
      the plain Unicode string

    :rtype: unicode
    """
    input = str(input)
    input_length = len(input)
    output = u""
    i = 0
    while i < input_length:
        c = input[i]
        if c in safe_characters:
            output += c
        elif c == "_":
            output += " "
        elif c == "{":
            i += 1
            while i < input_length and input[i] in lowercase_letters:
                output += input[i].upper()
                i += 1
            if i == input_length:
                # In you want to implement StreamReaders: If the string
                # didn't start with this parentheses sequence, it should
                # return from here with a smaller value for consumed_length
                handle_problematic_characters(errors, input, i-1, i, "open brace was never closed")
                continue
            if input[i] != '}':
                handle_problematic_characters(
                    errors, input, i, i+1, "invalid character '%s' in braces sequence" % input[i])
                continue
        elif c == "(":
            end_position = input.find(")", i)
            if end_position == -1:
                end_position = i+1
                while end_position < input_length and input[end_position] in "0123456789abcdef" and \
                        end_position - i <= 8:
                    end_position += 1
                # In you want to implement StreamReaders: If the string
                # didn't start with this curly braces sequence, it should
                # return from here with a smaller value for consumed_length
                output += handle_problematic_characters(errors, input, i, end_position,
                                                        "open parenthesis was never closed")
                i = end_position
                continue
            else:
                try:
                    output += unichr(int(input[i+1:end_position], 16))
                except:
                    output += handle_problematic_characters(errors, input, i, end_position+1,
                                                            "invalid data between parentheses")
            i = end_position
        else:
            output += handle_problematic_characters(errors, input, i, i+1, "invalid character '%s'" % c)
        i += 1
    return output, input_length

def registry(encoding):
    """Lookup function for the ``safefilename`` encoding.

    :Parameters:
      - `encoding`: the encoding which is looked for by the caller

    :type encoding: str

    :Return:
      a tuple containing (encoder, decoder, streamencoder, streamdecoder).  The
      latter two are set to ``None`` because they are not implemented (and not
      needed).

    :rtype: tuple
    """
    if encoding == "safefilename":
        return (encode, decode, None, None)
    else:
        return None

codecs.register(registry)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    doctest.testfile("../misc/safefilename.txt")
