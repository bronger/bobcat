#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import common

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.helpers"))
suite.addTest(doctest.DocFileSuite("helpers.txt"))
