#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test module for testing all doctests found in bobcatlib's modules.  This
module builds a text suite automatically from all doctests found in bobcatlib's
source code.  For doing this, it walks through the directory tree and looks
into almost all ``.py`` files.

Note that the doctests don't belong to the test canon of Bobcat.  They are only
tested so that the examples in the source files are correct, and only if
"--all" is given to ``test_all.py``.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, os.path, doctest
from . import common_test
import imp

suite = unittest.TestSuite()

def path_to_modulename(path):
    """Converts an absolute path to a Python file to a dotted module name.
    This only works for names in the `bobcatlib` package.

    :Parameters:
      - `path`: the absolute path to the Python source file.  The ``.py``
        extension must be truncated.

    :type path: str

    :Return:
      - the dotted modulename of the given file

    :rtype: str
    """
    modulename = ""
    while True:
        path, current_head = os.path.split(path)
        assert current_head != ""
        if current_head == "bobcatlib":
            return current_head + modulename
        else:
            modulename = "." + current_head + modulename

def is_backend_directory(path):
    """Returns whether the given path belongs to the backends section.

    :Parameters:
      - `path`: the absolute path that should be tested

    :type path: str

    :Return:
      - ``True`` if the path is part of the backends hierarchy so that Python
        code in it belongs to ackend code, and ``False`` otherwise

    :rtype: bool
    """
    while True:
        path, head = os.path.split(path)
        if head == "backends":
            return True
        elif not head:
            return False

def load_backend_module(name, directory):
    """Load a module in the backend section (i.e. below the ``"backends/"``
    subdirectory.  This is necessary because the paths in the backend section
    may contain unpleasent characters that cannot be used to load these
    modules via ``"import"``.

    :Parameters:
      - `name`: the name of the module, i.e. the filename without the ``.py``.
        It mustn't have non-ASCII characters.
      - `directory`: the path to the directory in which the module resides

    :type name: str
    :type directory: str

    :Return:
      - the loaded module

    :rtype: module
    """
    file_, pathname, description = imp.find_module(module_name, [directory])
    try:
        module = imp.load_module(module_name, file_, pathname, description)
    finally:
        if file_:
            file_.close()

modules_found = False
for directory, __, filenames in os.walk(os.path.join(common_test.rootpath, "bobcatlib")):
    module_names = [filename[:-3] for filename in filenames
                    if filename.endswith(".py") and filename != "__init__.py"]
    # Now I create "modules".  Note that this can be a list of *names* or a
    # list of *modules*.  "doctest.DocTestSuite" can handle both, so this is no
    # problem.
    if is_backend_directory(directory):
        modules = []
        for module_name in module_names:
            module = load_backend_module(module_name, directory)
            modules.append(module)
    else:        
        modules = [path_to_modulename(os.path.join(directory, module_name))
                   for module_name in module_names]
    for module in modules:
        modules_found = True
        suite.addTest(doctest.DocTestSuite(module))
assert modules_found
