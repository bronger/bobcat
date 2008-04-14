#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import emitter

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.emitter"))

