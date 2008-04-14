#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import preprocessor

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.preprocessor"))
suite.addTest(doctest.DocFileSuite("preprocessor.txt"))
