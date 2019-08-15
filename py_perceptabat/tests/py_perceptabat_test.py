#!/usr/bin/env python

import unittest
from py_perceptabat import py_perceptabat

class py_perceptabat_test(unittest.TestCase):
    def test_single_thread(self):
        self.assertIsInstance(py_perceptabat(smiles_filepath='test_compounds.smi',
            logd_ph=7.4, threads=1, logp_algo='classic', pka_algo='classic',
            logd_algo='classic-classic'), dict)
        os.remove('test_compounds_results.csv')

    def test_multi_thread(self):
        self.assertIsInstance(py_perceptabat(smiles_filepath='test_compounds.smi',
            logd_ph=7.4, threads=3, logp_algo='classic', pka_algo='classic',
            logd_algo='classic-classic'), dict)
        os.remove('test_compounds_results.csv')

if __name__ == '__main__':
    unittest.main()
