#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script for executing all tests of the Bobcat program.  This is the script
which is executed my the "make tests" target in Bobcat's main Makefile.

If you pass ``--all`` to this script, it also tests all doctests in (almost)
all source code files and does further things.  Without ``--all``, it just runs
all test suites for the modules.
"""

import unittest, sys
from tests import common_test
from bobcatlib.settings import settings

settings["quiet"] = True

class TestSampleDocument(unittest.TestCase):
    

# Build test suite
from tests import test_common, test_helpers, test_preprocessor, test_settings, test_safefilename, \
    test_i18n, test_emitter, test_latex_substitutions
suite = unittest.TestSuite([test_common.suite,
                            test_helpers.suite,
                            test_preprocessor.suite,
                            test_settings.suite,
                            test_safefilename.suite,
                            test_i18n.suite,
                            test_emitter.suite,
                            test_latex_substitutions.suite])
if len(sys.argv) > 1 and sys.argv[1] == "--all":
    from tests import test_doctests
    suite.addTest(test_doctests.suite)
    # FixMe: Add epydoc generating test, and document processing tests

# Run the tests
common_test.chdir_to_testbed()
runner = unittest.TextTestRunner()
runner.run(suite)
