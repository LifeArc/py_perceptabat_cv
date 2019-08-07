#!/usr/bin/env python

# Author: Aretas Gaspariunas

# todo: support for pKa training, find a way to get .PCD file for training, use something other than sys for arg input

import os
import subprocess
from threading import Thread
from typing import Dict, Optional
import shutil
import csv
import sys

def py_perceptabat(smiles_filepath: str = 'dump.smi', logd_ph: float = 7.4,
    parallel: bool = False, threads: int = 4, logp_algo: str = 'classic',
    pka_algo: str = 'classic', logd_algo: str = 'classic-classic',
    logp_train: Optional[str] = None) -> Dict[str, Dict[str, str]]:

    '''
    #py_perceptabat
    Python wrapper function for ACD perceptabat_cv with parallel processing support.

    ##Description
    Calculates logP, logD, most acidic and basic apparent pKa and sigma using classic, GALAS or consensus algorithms.
    Supports multithreading.
    Results are returned as a dictioanry and are written to a CSV file.
    No non-standard lib package dependencies.
    Tested with Python 3.7.2.

    ##Example usage from CLI:
    python py_perceptabat.py <input_filepath> <logD pH> <boolean for parallelization> <number of cores> <logP algorithm> <pKa alogrithm> <logD algorithms>
    e.g. python py_perceptabat.py <input_filepath> 7.4 True 4 classic classic classic-classic

    ##Arguments
    Set smiles_filepath to specify SMILES input file. The file must have two columns: SMILES and ID separated by a space;
    Set logd_ph to define at which pH logD will be calculated;
    Set parallel=True to enable parallelization using threading;
    Set threads argument to specify the number of threads for parallelization. Inactive if parallel=False;
    Set *_algo arguments to specify algorithm for each property prediction.
    LogD predictions use logp and pka properties and algorithms for both respecitvely must be provided e.g. classic-galas. Please refer to ACD documentation for more details;
    Set logp_train to specify .PCD training file for logP prediction.

    NOTE: training from CLI is currently disabled.
    '''

    COLUMNS = []
    MAIN_PATH = os.path.dirname(os.path.realpath(__file__))

    # converting arguments to actual booleans
    bool_trans = {'True':True, 'False':False}
    if parallel in bool_trans:
        parallel = bool_trans[parallel]

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

    def percepta_cmd(filename, logp_train=logp_train):

        algo_dict = {
            'logp':{"classic":"-OLOGPALGA", "galas":"-OLOGPALGGALAS","consensus":"-OLOGPALGCONSENSUS"},
            'pka':{"classic":"-MPKAAPP","galas":"-MPKAAPPGALAS"},
            'logd':{"classic-classic":"-OLOGDALGCLASS", "classic-galas":"-OLOGDALGCLASSGALAS",
                "galas-classic":"-OLOGDALGGALASCLASS","galas-galas":"-OLOGDALGGALAS",
                "consensus-classic":"-OLOGDALGCONSCLASS","consensus-galas":"-OLOGDALGCONSGALAS"}
        }

        cmd_list = ["perceptabat_cv", "-OOVERWRITE", "-MLOGP", algo_dict['logp'][logp_algo.lower()],
            "-TLOGP", "-MLOGD", "-OLOGDPH1{0}".format(logd_ph), algo_dict['logd'][logd_algo.lower()],
            "-TLOGD", algo_dict['pka'][pka_algo.lower()], "-TPKA", "-OPKAMOST", "-OOUTSPLITACIDBASIC",
            "-MSIGMA", "-TSIGMA", "-TFNAME{0}.result".format(filename)]

        logp_train = None if logp_train == 'None' else logp_train
        if logp_train is not None:
            cmd_list.append("-ULOGP{}".format(logp_train))
        cmd_list.append(filename)

        # subprocess.Popen(cmd_list).wait()
        subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT).wait()

    def parse_acd_output(result, offset=0):

        parsed_output = {}

        for line in result:
            if (line.split()[0].isdigit() and line.split()[1] != 'ID:' and
                not line.split()[1].lower().endswith('caution:')):
                cp_id = str(int(line.split()[0]) + offset)
                value = line.split(': ')[1].rstrip('\n')
                if not cp_id in parsed_output:
                    parsed_output[cp_id] = {}
                parsed_output[cp_id][line.split()[1].rstrip(':').lower()] = value
            else:
                continue

        # creating missing keys
        counter = 0
        for key, value in parsed_output.items():
            for col, value1 in value.items():
                if col not in COLUMNS:
                    COLUMNS.append(col)
            counter += 1
            if counter > 100:
                break
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
    elif parallel is False:
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
        parallel=sys.argv[3], threads=int(sys.argv[4]), logp_algo=sys.argv[5],
        pka_algo=sys.argv[6], logd_algo=sys.argv[7], logp_train=None)
