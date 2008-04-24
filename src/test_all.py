#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script for executing all tests of the Bobcat program.  This is the script
which is executed my the "make tests" target in Bobcat's main Makefile.

If you pass ``--all`` to this script, it also tests all doctests in (almost)
all source code files and does further things.  Without ``--all``, it just runs
all test suites for the modules.
"""

import unittest, sys, subprocess, os
from tests import common_test
from bobcatlib.settings import settings

settings["quiet"] = True

class TestSampleDocument(unittest.TestCase):
    """Test case for a sample document run through Bobcat.
    """
    def test(self):
        """sample document should run through with expected output"""
        result = subprocess.call(["python", "../bobcat.py", "test1.bcat"])
        self.assertEqual(result, 0, "bobcat process aborted")
        actual_output = open("test1.tex").read()
        desired_output = open("test1-desired.tex").read()
        self.assertEqual(actual_output, desired_output,
                         "result of sample document was not the expected result")
        os.remove("test1.tex")
        os.remove("bobcat.log")

class TestDocumentation(unittest.TestCase):
    """Test case for the Epydoc documentation, whether it is correct.
    """
    def setUp(self):
        os.chdir("..")
    def test(self):
        """docstrings for Epydoc documentation should be correct"""
        epydoc = subprocess.Popen(["epydoc", "--config=../misc/epydoc.cfg"], stdout=subprocess.PIPE)
        result = epydoc.wait()
        self.assertEqual(result, 0, "Epydoc had errors")
        os.remove("tests/test1.tex")
        os.remove("bobcat.log")
    def tearDown(self):
        os.chdir("tests")

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
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestSampleDocument))
    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestDocumentation))

# Run the tests
common_test.chdir_to_testbed()
runner = unittest.TextTestRunner()
runner.run(suite)
