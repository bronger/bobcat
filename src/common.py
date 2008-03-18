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

"""Module for things that are used by (almost) all parts of Gummi.  This is
most notably the Exception classes and logging.

:var modulepath: path to the directory where gummi.py resides
:var preferred_encoding: the default shell encoding on the current machine

:type modulepath: str
:type preferred_encoding: str
"""

import re, sys, os.path, logging

modulepath = os.path.abspath(os.path.dirname(sys.argv[0]))
if 'epydoc' in sys.modules:
    modulepath = os.path.abspath("src/")

class PositionMarker(object):
    """A mere container for a position in a original document, which is a
    unicode string.  Its main purpose is for generating expressive error
    messages with the exact position in the source document where the error was
    detected.  It is used primarily in `preprocessor.Excerpt` in order to keep
    track of the origins of the different party of excerpts, after applying
    input methods and slicing and such.

    This would be a struct in C and a record in Pascal.

    :ivar url: URL of the file from which this position comes
    :ivar linenumber: linenumber (starting with 1) of the line from which
      this position comes
    :ivar column: column (starting with 0) within the file where this
      position is found
    :ivar index: index within original_text of the Excerpt this
      PositionMarker belongs to where this position is found

    :type url: str
    :type linenumber: int
    :type column: int
    :type index: int
    """
    def __init__(self, url, linenumber, column, index):
        self.url = url
        self.linenumber = linenumber
        self.column = column
        self.index = index
    def __repr__(self):
        return 'PositionMarker("%s", %d, %d, %d)' % \
            (self.url, self.linenumber, self.column, self.index)
    def __str__(self):
        return 'file "%s", line %d, column %d' % (self.url, self.linenumber, self.column)
    def __cmp__(self, other):
        """The `index` must not be included in the decision whether two PositionMarkers
        are the same."""
        return cmp((self.url, self.linenumber, self.column),
                   (other.url, other.linenumber, other.column))
    def transpose(self, offset):
        """Return a new PositionMarker instance in order to get rid of side
        effect problems, by forcing making a *copy*.  Additionally, index
        is adjusted by `offset`, which is used in the slicing, indexing and
        concatenation routines of `preprocessor.Excerpt`.

        :Parameters:
          - `offset`: the offset that is added to the index attribute of
            the generated PositionMarker instance.  May be positive or
            negative or zero.

        :type offset: int

        :Return:
          a newly created PositionMarker instance

        :rtype: PositionMarker
        """
        return PositionMarker(self.url, self.linenumber, self.column,
                                      self.index+offset)

class Error(Exception):
    """Standard error class.
    """
    def __init__(self, description):
        """
        :Parameters:
          - `description`: error message

        :type description: unicode
        """
        self.description = description
        # FixMe: The following must be made OS-dependent
        Exception.__init__(self, description.encode("utf-8"))

class LocalVariablesError(Error):
    """Error class for malformed lines with the local variables.
    """
    def __init__(self, description):
        """
        :Parameters:
          - `description`: error message

        :type description: unicode
        """
        super(LocalVariablesError, self).__init__(description)

class FileError(Error):
    """Error class for errors in a Gummi file.
    """
    def __init__(self, description, position_marker):
        """
        :Parameters:
          - `description`: error message
          - `position_marker`: the exact position where the error occured

        :type description: unicode
        :type position_marker: PositionMarker
        """
        super(FileError, self).__init__(str(position_marker) + ": " + description)

class EncodingError(FileError):
    """Error class for encoding errors in a Gummi file.
    """
    def __init__(self, description, position_marker):
        """
        :Parameters:
          - `description`: error message
          - `position_marker`: the exact position where the error occured

        :type description: unicode
        :type position_marker: PositionMarker
        """
        super(EncodingError, self).__init__(description, position_marker)

class KeyValueError(FileError):
    """Error class for errors in key/value lists in a Gummi file.
    """
    def __init__(self, description, position_marker):
        """
        :Parameters:
          - `description`: error message
          - `position_marker`: the exact position where the error occured

        :type description: unicode
        :type position_marker: PositionMarker
        """
        super(KeyValueError, self).__init__(str(position_marker) + ": " + description,
                                            position_marker)

def parse_local_variables(first_line, force=False, comment_marker=r"\.\. "):
    r"""Treats first_line as a line with local variables and extracts the
    key--value pairs from it.  Note that both first_line and the resulting
    dictionary contain plain strings and no unicode strings because the local
    variables are read at a time when the file encoding is still unclear.
    That's also the reason why only ASCII characters are allowed here.

        >>> parse_local_variables(".. -*- coding: utf-8; Blah: Blubb -*-\n")
        {'blah': 'blubb', 'coding': 'utf-8'}
        >>> parse_local_variables("This is not a local variables line")
        {}
        >>> parse_local_variables("; -*- coding: utf-8 -*-\n")
        {}
        >>> parse_local_variables("; -*- coding: utf-8 -*-\n", comment_marker="(#|;)")
        {'coding': 'utf-8'}

    :Parameters:
      - `first_line`: line to be parsed as a local variables line
      - `force`: if True, first_line must be a local variables line.
        Otherweise, it may also be something completely different.  This is
        important for exceptions being raised.
      - `comment_marker`: regular expression for the symbol or symbol sequence
        which marks comment lines.  Since the local variables are stored
        technically in a comment line, this routine must know it.

    :type first_line: string
    :type force: bool
    :type comment_marker: str

    :Return:
      A dictionary with the key--value pairs.  Both are strings.  If the value
      was a comma-separated list, it is a list of strings instead of a string.
      An empty dictionary if the line doesn't look like a local variables line
      at all.

    :rtype: dict

    :Exceptions:
      - `LocalVariablesError`: if the line looks like a local variables line
        but has not a valid local variables line format
    """
    local_variables_match = re.match(comment_marker+r"\s*-\*-\s*(?P<variables>.+)\s*-\*-\Z",
                                     first_line.rstrip().lower())
    if not local_variables_match:
        if force:
            raise LocalVariablesError(u"Malformed local variables line")
        else:
            return {}
    items = local_variables_match.group("variables").split(";")
    valid_pattern = re.compile(r"[a-z0-9_-]+\Z")
    local_variables = {}
    for item in items:
        if item.strip() == "":
            continue
        try:
            key, value = item.split(":")
        except:
            raise LocalVariablesError(u"Malformed local variables line")
        key, value = key.strip(), value.strip()
        if not valid_pattern.match(key):
            raise LocalVariablesError(u"Malformed key '%s' in local variables line"
                                      % key.decode("latin-1"))
        if "," in value:
            value = value.split(",")
            # FixMe: Isn't it necessary to strip whitespace from all items in
            # `value`?
            for subvalue in value:
                if not valid_pattern.match(subvalue):
                    raise LocalVariablesError(u"Malformed value '%s' local variables line"
                                              % subvalue.decode("latin-1"))
        elif not valid_pattern.match(value):
            raise LocalVariablesError(u"Malformed value '%s' local variables line"
                                      % value.decode("latin-1"))
        local_variables[key] = value
    return local_variables

def setup_logging(logfile_name=None, do_logging=True, level=logging.DEBUG):
    """Start the logging facility if the caller whishes this.  Every module in
    Gummi can then write to the logfile by saying::

        import logging
        logger = logging.getLogger("gummi.module.submodule")
        logger.error("Something went wrong")

    By the way, ``getLogger`` returns a singleton object, so everything really
    goes into the same logfile.

    :Parameters:
      - `logfile_name`: file name of the logfile.  Don't do logging if this is
        ``None``.
      - `do_logging`: do logging only if this is ``True``
      - `level`: logging level, see
        http://docs.python.org/lib/module-logging.html

    :type logfile_name: str
    :type do_logging: bool
    :type level: int
    """
    # pylint: disable-msg=C0111
    if do_logging and logfile_name:
        logging.basicConfig(level=level, filename=logfile_name, filemode="w",
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            format="%(asctime)s %(name)s %(levelname)-8s %(message)s")
    else:
        class LogSink(object):
            def write(self, *args, **kwargs):
                pass
            def flush(self, *args, **kwargs):
                pass
        logging.basicConfig(stream=LogSink())

class ParseError(Error):
    """Generic error class for parse errors and warnings.  At the same time,
    the class holds the list with all errors and warnings.

    This class is special in two respects: First, it isn't raised usually;
    instead, its instances are appended to `parse_errors`.  And secondly, it
    can also be a warning.  However, it would be awkward and useless to use
    Python's warning facility for parser warnings, too.

    :cvar parse_errors: all errors and warnings during the last parsing run.
      This variable is to be used by external modules that are interested in
      the result of the parsing process.
    :cvar logger: logger instance for parser messages

    :ivar provoking_element: the document element in which the error or warning
      occured
    :ivar type: if ``"error"``, it is an error; if ``"warning"``, it is a
      warning
    :ivar position: where the error or warning occured

    :type parse_errors: list of `ParseError`
    :type logger: logging.Logger
    :type provoking_element: `parser.Node`
    :type type: str
    :type position: `PositionMarker`
    """
    logger = logging.getLogger("gummi.parser")
    parse_errors = []
    def __init__(self, provoking_element, description, type_="error", position_marker=None):
        """
        :Parameters:
          - `provoking_element`: the document element in which the error
            occured
          - `description`: error message
          - `type_`: if ``"error"``, it is an error; if ``"warning"``, it is a
            warning
          - `position_marker`: if given, it denotes the exact position in the
            document where the error occured

        :type provoking_element: `parser.Node`
        :type description: unicode
        :type `type_`: str
        :type position_marker: `PositionMarker`
        """
        super(ParseError, self).__init__(description)
        assert type_ in ["error", "warning"]
        self.provoking_element, self.type, self.position = \
            provoking_element, type_, position_marker or provoking_element.position
    def __str__(self):
        # FixMe: The following must be made OS-dependent
        return unicode(self).encode("utf-8")
    def __unicode__(self):
        return u"%s: %s" % (self.position, self.description)

def add_parse_error(parse_error):
    r"""Adds en error or warning to the list of errors and warnings.  It
    also writes it to the log file and to stderr, if this hasn't be changed by
    the user.

    :Parameters:
      - `parse_error`: the actual parse error

    :type parse_error: `ParseError`

        >>> import parser, preprocessor, settings
        >>> import os.path
        >>> os.chdir(os.path.join(modulepath, "../misc/"))
        >>> setup_logging()
        >>> open("test2.rsl", "w").write(".. -*- coding: utf-8 -*-\n.. Gummi 1.0\n"
        ... "Dummy document.\n")
        >>> text, __, __ = preprocessor.load_file("test2.rsl")
        >>> node = parser.Node(None)
        >>> node.parse(text, 0)
        0
        >>> settings.settings["quiet"] = True
        >>> node.throw_parse_error("test error message")
        >>> parser.common.ParseError.parse_errors
        [ParseError('test error message',)]
    """
    assert isinstance(parse_error, ParseError)
    ParseError.parse_errors.append(parse_error)
    message = unicode(parse_error)
    if parse_error.type == "error":
        ParseError.logger.error(message)
        import settings
        if not settings.settings["quiet"]:
            print>>sys.stderr, message
    else:
        ParseError.logger.warning(message)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    doctest.testfile("../misc/common.txt")
