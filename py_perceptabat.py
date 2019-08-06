#!/usr/bin/env python

# Author: Aretas Gaspariunas

# todo: GALAS algorithm support; training using in-house data -ULOGP; write all columns to csv

import os
import subprocess
from threading import Thread
from typing import Dict
import shutil
import csv
import sys

def py_perceptabat(smiles_filepath: str = 'dump.smi', logd_ph: float = 7.4,
    parallel: bool = False, threads: int = 4) -> Dict[str, Dict[str, str]]:

    '''
    Python wrapper function for ACD perceptabat_cv with parallel processing support.
    Calculates logP, logD, and most acidic and basic pKa using classic algorithm.
    Supports multithreading.
    Results are written to a CSV file.
    No non-standard lib package dependencies.
    Tested with Python 3.7.2.

    Arguments:
    Set smiles_filepath to specify SMILES input file. The file must have two columns: SMILES and ID separated by a space;
    Set logd_ph to define at which pH logD will be calculated;
    Set parallel=True to enable parallelization using threading;
    Set threads argument to specify the number of threads for parallelization. Inactive if parallel=False.

    Example usage from CLI:
    python py_perceptabat.py <input_filepath> <logD pH> <boolean for parallelization> <number of cores>
    e.g. python py_perceptabat.py <input_filepath> 7.4 True 4
    '''

    COLUMNS = ['acd_logp', 'acd_logd_ph', 'acd_logd', 'acd_acid_pka', 'acd_basic_pka']
    MAIN_PATH = os.path.dirname(os.path.realpath(__file__))

    def create_trans_dict(input_file):

        try:
            translation_dict = {}
            with open(input_file, 'r') as f:

                # testing the format of input file
                if len(f.readline().split()) != 2:
                    raise ValueError("Input file should contain two columns in format 'SMILES_col ID_col.")
                f.seek(0)

                counter = 1
                for line in f:
                    smiles, id_ = line.split()
                    translation_dict[str(counter)] = id_
                    counter += 1

            return translation_dict

        except FileNotFoundError:
            raise

    def split_file(filepath, chunksize=5000):

        with open(filepath, 'rb') as file_obj:

            line_count = 0
            file_count = 0

            chunked_file_object = open(filepath.split('.')[0]+'__chunk__'+
                str(file_count)+'.'+filepath.split('.')[1],"wb")
            for line in file_obj:
                chunked_file_object.write(line)
                line_count += 1
                if line_count == chunksize:
                    chunked_file_object.close()
                    file_count += 1
                    line_count = 0
                    chunked_file_object = open(filepath.split('.')[0]+'__chunk__'+
                        str(file_count)+'.'+filepath.split('.')[1],"wb")

            chunked_file_object.close()

            if line_count == 0:
                os.remove(filepath.split('.')[0]+'__chunk__'+
                    str(file_count)+'.'+filepath.split('.')[1])

    def percepta_cmd(filename):

        subprocess.Popen(["perceptabat_cv", "-OOVERWRITE", "-MLOGP", "-TLOGP",
            "-MLOGD", "-OLOGDPH1{0}".format(logd_ph), "-TLOGD", "-MPKASINGLE",
            "-TPKA", "-OPKAMOST", "-OOUTSPLITACIDBASIC", "-TFNAME{0}.result".format(filename),
            filename], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()

    def parse_acd_output(result, offset=0):

        # todo: include all information
        parsed_output = {}

        for line in result:
            if 'ACD_LogP:' in line:
                cp_id = str(int(line.split()[0]) + offset)
                logp = line.split(': ')[1].rstrip('\n')
                if not cp_id in parsed_output:
                    parsed_output[cp_id] = {}
                parsed_output[cp_id]['acd_logp'] = logp
            elif 'ACD_LogD_pH:' in line:
                cp_id = str(int(line.split()[0]) + offset)
                ph = line.split(': ')[1].rstrip('\n')
                if not cp_id in parsed_output:
                    parsed_output[cp_id] = {}
                parsed_output[cp_id]['acd_logd_ph'] = ph
            elif 'ACD_LogD:' in line:
                cp_id = str(int(line.split()[0]) + offset)
                logd = line.split(': ')[1].rstrip('\n')
                if not cp_id in parsed_output:
                    parsed_output[cp_id] = {}
                parsed_output[cp_id]['acd_logd'] = logd
            elif 'ACD_pKa_Acidic_Single_1:' in line:
                cp_id = str(int(line.split()[0]) + offset)
                acid_pka = line.split(': ')[1].rstrip('\n')
                if not cp_id in parsed_output:
                    parsed_output[cp_id] = {}
                parsed_output[cp_id]['acd_acid_pka'] = acid_pka
            elif 'ACD_pKa_Basic_Single_1:' in line:
                cp_id = str(int(line.split()[0]) + offset)
                basic_pka = line.split(': ')[1].rstrip('\n')
                if not cp_id in parsed_output:
                    parsed_output[cp_id] = {}
                parsed_output[cp_id]['acd_basic_pka'] = basic_pka
            else:
                continue

        for key, value in parsed_output.items():
            for col in COLUMNS:
                if col not in value:
                    parsed_output[key][col] = 'NaN'

        return parsed_output

    if shutil.which('perceptabat_cv') is None:
        raise OSError('Failed to execute perceptabat_cv.')

    # checking if arguments match conditions
    if '__' in smiles_filepath or ' ' in smiles_filepath:
        raise ValueError("Please do not use '__' or space characters in input file name.")

    # creating translation dictionary for IDs and checking input file
    translation_dict = create_trans_dict(smiles_filepath)

    # running with threading
    if parallel is True:

        if isinstance(threads, int) and threads > 0:
            pass
        else:
            raise ValueError("Please use positive integer for threads argument.")

        # checking the number of cores
        from multiprocessing import cpu_count
        if cpu_count() < threads:
            raise ValueError('{0} cores detected. Can not spawn more threads '
                'than existing cores.'.format(cpu_count()))

        # counting number of lines in input files
        num_lines = sum(1 for line in open(smiles_filepath))
        chunksize = int(int(num_lines) / threads)

        # split the input file into chunks
        split_file(smiles_filepath, chunksize=chunksize)
        split_file_list = [i for i in os.listdir(MAIN_PATH) if 'chunk' in i]

        # spawning threads
        th = []
        for index, file in enumerate(split_file_list):
            t = Thread(target=percepta_cmd, args=(os.path.join(MAIN_PATH,file),))
            th.append(t)
            th[index].start()

        for t in th:
            t.join()

        # parsing chunks
        result_dict = {}
        for i in os.listdir(MAIN_PATH):
            if '__chunk__' and '.result' in i:

                chunk_no = int(i.split('__')[2].split('.')[0])

                with open(os.path.join(MAIN_PATH, i), 'r') as output_file:
                    temp_result_dict = parse_acd_output(output_file, offset=chunk_no*chunksize)
                    result_dict.update(temp_result_dict)

            # remove chunk files
            if '__chunk__' in i:
                os.remove(os.path.join(MAIN_PATH, i))

    # running without threading
    else:
        percepta_cmd(smiles_filepath)

        with open('{0}.result'.format(smiles_filepath), 'r') as output_file:
            result_dict = parse_acd_output(output_file)

        os.remove('{0}.result'.format(smiles_filepath))

    # translating dict ids
    trans_result_dict = {}
    for cp_id, props in result_dict.items():
        trans_result_dict[translation_dict[cp_id]] = props

    # writting to csv
    COLUMNS.append('compound_id')
    with open("{0}_results.csv".format(smiles_filepath.split('.')[0]), "w") as f:
        w = csv.DictWriter(f, COLUMNS)
        w.writeheader()
        for k in trans_result_dict:
            w.writerow({col: trans_result_dict[k].get(col) or k for col in COLUMNS})

    return trans_result_dict

if __name__ == "__main__":

    py_perceptabat(smiles_filepath=sys.argv[1], logd_ph=float(sys.argv[2]),
        parallel=eval(sys.argv[3]), threads=int(sys.argv[4]))
