#!/usr/bin/env python

import unittest
import os
from py_perceptabat_cv import py_perceptabat_cv

class py_perceptabat_test(unittest.TestCase):

    def test_single_thread(self):
        result = py_perceptabat_cv("-OOVERWRITE -MLOGP -OLOGPALGA -TLOGP -MLOGD "
            "-OLOGDPH17.4 -OLOGDALGCONSCLASS -TLOGD -MPKAAPP -TPKA -OPKAMOST "
            "-OOUTSPLITACIDBASIC -MSIGMA -TSIGMA -TFNAMEcompounds_results.csv compounds.smi", threads=1)
        os.remove('compounds_results.csv')

        self.assertIsInstance(result, dict)

    def test_multi_thread(self):
        result = py_perceptabat_cv("-OOVERWRITE -MLOGP -OLOGPALGA -TLOGP -MLOGD "
            "-OLOGDPH17.4 -OLOGDALGCONSCLASS -TLOGD -MPKAAPP -TPKA -OPKAMOST "
            "-OOUTSPLITACIDBASIC -MSIGMA -TSIGMA -TFNAMEcompounds_results.csv compounds.smi", threads=2)
        os.remove('compounds_results.csv')

        self.assertIsInstance(result, dict)

    def test_multi_dir_input(self):
        result = py_perceptabat_cv("-OOVERWRITE -MLOGP -OLOGPALGA -TLOGP -MLOGD "
            "-OLOGDPH17.4 -OLOGDALGCONSCLASS -TLOGD -MPKAAPP -TPKA -OPKAMOST "
            "-OOUTSPLITACIDBASIC -MSIGMA -TSIGMA -TFNAMEcompounds_results.csv ../tests/compounds.smi", threads=2)
        os.remove('compounds_results.csv')

        self.assertIsInstance(result, dict)

if __name__ == '__main__':

    unittest.main()
