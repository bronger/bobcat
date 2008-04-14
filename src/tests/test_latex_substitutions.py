#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import latex_substitutions

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.latex_substitutions"))

