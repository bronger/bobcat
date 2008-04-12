import unittest
import doctest

import sys, os.path
testmodule_path = os.path.dirname(__file__)
rootpath = os.path.split(testmodule_path)[0]
sys.path.append(rootpath)

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("gummi.preprocessor"))
suite.addTest(doctest.DocTestSuite("gummi.common"))
suite.addTest(doctest.DocTestSuite("gummi.settings"))
suite.addTest(doctest.DocTestSuite("gummi.safefilename"))
suite.addTest(doctest.DocTestSuite("gummi.i18n"))
suite.addTest(doctest.DocTestSuite("gummi.helpers"))
suite.addTest(doctest.DocTestSuite("gummi.emitter"))
suite.addTest(doctest.DocTestSuite("gummi.latex_substitutions"))

suite.addTest(doctest.DocFileSuite("common.txt"))
suite.addTest(doctest.DocFileSuite("helpers.txt"))
suite.addTest(doctest.DocFileSuite("safefilename.txt"))
suite.addTest(doctest.DocFileSuite("settings.txt"))
suite.addTest(doctest.DocFileSuite("preprocessor.txt"))

runner = unittest.TextTestRunner()
os.chdir(testmodule_path)
runner.run(suite)
