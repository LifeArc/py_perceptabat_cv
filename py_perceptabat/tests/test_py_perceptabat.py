#!/usr/bin/env python

import unittest
import os
from py_perceptabat import py_perceptabat

class py_perceptabat_test(unittest.TestCase):

    def test_single_thread(self):
        result = py_perceptabat(smiles_filepath='compounds.smi',
            logd_ph=7.4, threads=1, logp_algo='classic', pka_algo='classic',
            logd_algo='classic-classic')
        os.remove('compounds_results.csv')

        self.assertIsInstance(result, dict)

    def test_multi_thread(self):
        result = py_perceptabat(smiles_filepath='compounds.smi',
            logd_ph=7.4, threads=2, logp_algo='classic', pka_algo='classic',
            logd_algo='classic-classic')
        os.remove('compounds_results.csv')

        self.assertIsInstance(result, dict)

    def test_multi_thread_training(self):
        result = py_perceptabat(smiles_filepath='compounds.smi',
            logd_ph=7.4, threads=2, logp_algo='classic', pka_algo='classic',
            logd_algo='classic-classic', logp_train='TRAIN2.PCD')
        os.remove('compounds_results.csv')

        self.assertIsInstance(result, dict)

if __name__ == '__main__':
    unittest.main()
