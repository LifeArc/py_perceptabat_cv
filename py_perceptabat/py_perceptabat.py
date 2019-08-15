#!/usr/bin/env python

# Author: Aretas Gaspariunas

import os
import subprocess
from threading import Thread
from typing import Dict, Optional
import shutil
import csv

def py_perceptabat(smiles_filepath: str = 'dump.smi', logd_ph: float = 7.4,
    threads: int = 1, logp_algo: str = 'classic', pka_algo: str = 'classic',
    logd_algo: str = 'classic-classic', logp_train: Optional[str] = None) -> Dict[str, Dict[str, str]]:

    ACD_COLUMNS = []
    main_path = os.path.dirname(os.path.realpath(__file__))

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
                str(file_count)+'.'+filepath.split('.')[1], "wb")
            for line in file_obj:
                chunked_file_object.write(line)
                line_count += 1
                if line_count == chunksize:
                    chunked_file_object.close()
                    file_count += 1
                    line_count = 0
                    chunked_file_object = open(filepath.split('.')[0]+'__chunk__'+
                        str(file_count)+'.'+filepath.split('.')[1], "wb")

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
                'caution' not in line.split()[1].lower() and
                'warning' not in line.split()[1].lower()):

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
                if col not in ACD_COLUMNS:
                    ACD_COLUMNS.append(col)
            counter += 1
            if counter > 2000:
                break
        for key, value in parsed_output.items():
            for col in ACD_COLUMNS:
                if col not in value:
                    parsed_output[key][col] = 'NaN'

        return parsed_output

    def parsing_chunks(path, chunksize):

        # parsing chunks
        result_dict = {}
        for i in os.listdir(path):
            if '__chunk__' and '.result' in i:

                chunk_no = int(i.split('__')[2].split('.')[0])

                with open(os.path.join(path, i), 'r') as output_file:
                    temp_result_dict = parse_acd_output(output_file, offset=chunk_no*chunksize)
                    result_dict.update(temp_result_dict)

            # remove chunk files
            if '__chunk__' in i:
                os.remove(os.path.join(path, i))

        return result_dict

    # argument sanity check
    if shutil.which('perceptabat_cv') is None:
        raise OSError('Failed to execute perceptabat_cv.')

    if '__' in smiles_filepath or ' ' in smiles_filepath:
        raise ValueError("Please do not use '__' or space characters in input file name.")

    if isinstance(threads, int) and threads > 0:
        pass
    else:
        raise ValueError("Please use positive integer for threads argument.")

    from multiprocessing import cpu_count
    if cpu_count() < threads:
        raise ValueError('{0} cores detected. Can not spawn more threads '
            'than existing cores.'.format(cpu_count()))

    # creating translation dictionary for IDs and checking input file
    translation_dict = create_trans_dict(smiles_filepath)

    # running with threading
    if int(threads) > 1:
        # counting number of lines in input files
        num_lines = sum(1 for line in open(smiles_filepath))
        chunksize = int(int(num_lines) / threads)

        # split the input file into chunks
        split_file(smiles_filepath, chunksize=chunksize)
        split_file_list = [i for i in os.listdir(main_path) if 'chunk' in i]

        # spawning threads
        th = []
        for index, file in enumerate(split_file_list):
            t = Thread(target=percepta_cmd, args=(os.path.join(main_path,file),))
            th.append(t)
            th[index].start()

        for t in th:
            t.join()

        # parsing chunks
        result_dict = parsing_chunks(main_path, chunksize)

    # running without threading
    elif int(threads) == 1:
        percepta_cmd(smiles_filepath)

        with open('{0}.result'.format(smiles_filepath), 'r') as output_file:
            result_dict = parse_acd_output(output_file)

        os.remove('{0}.result'.format(smiles_filepath))

    # translating dict ids
    trans_result_dict = {}
    for cp_id, props in result_dict.items():
        trans_result_dict[translation_dict[cp_id]] = props

    # writting to csv
    ACD_COLUMNS.append('compound_id')
    with open("{0}_results.csv".format(smiles_filepath.split('.')[0]), "w") as f:
        w = csv.DictWriter(f, ACD_COLUMNS)
        w.writeheader()
        for k in trans_result_dict:
            w.writerow({col: trans_result_dict[k].get(col) or k for col in ACD_COLUMNS})

    return trans_result_dict

if __name__ == "__main__":

    import sys

    py_perceptabat(smiles_filepath=sys.argv[1], logd_ph=float(sys.argv[2]),
        threads=int(sys.argv[3]), logp_algo=sys.argv[4], pka_algo=sys.argv[5],
        logd_algo=sys.argv[6], logp_train=None)
