#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import safefilename

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.safefilename"))
suite.addTest(doctest.DocFileSuite("safefilename.txt"))
