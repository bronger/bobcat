# -*- coding: utf-8 -*-
# This file is Python 2.7.

import sys, os.path
testmodules_path = os.path.dirname(os.path.abspath(__file__))
rootpath = os.path.split(testmodules_path)[0]
sys.path.append(rootpath)

def chdir_to_testbed():
    os.chdir(testmodules_path)
