#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2007, 2008 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Bobcat program.
#
#    Bobcat is free software; you can redistribute it and/or modify it under
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

import unittest
import doctest

import sys, os.path
testmodule_path = os.path.dirname(os.path.abspath(__file__))
rootpath = os.path.split(testmodule_path)[0]
sys.path.append(rootpath)

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.preprocessor"))
suite.addTest(doctest.DocTestSuite("bobcatlib.common"))
suite.addTest(doctest.DocTestSuite("bobcatlib.settings"))
suite.addTest(doctest.DocTestSuite("bobcatlib.safefilename"))
suite.addTest(doctest.DocTestSuite("bobcatlib.i18n"))
suite.addTest(doctest.DocTestSuite("bobcatlib.helpers"))
suite.addTest(doctest.DocTestSuite("bobcatlib.emitter"))
suite.addTest(doctest.DocTestSuite("bobcatlib.latex_substitutions"))

suite.addTest(doctest.DocFileSuite("common.txt"))
suite.addTest(doctest.DocFileSuite("helpers.txt"))
suite.addTest(doctest.DocFileSuite("safefilename.txt"))
suite.addTest(doctest.DocFileSuite("settings.txt"))
suite.addTest(doctest.DocFileSuite("preprocessor.txt"))

runner = unittest.TextTestRunner()
os.chdir(testmodule_path)
runner.run(suite)
