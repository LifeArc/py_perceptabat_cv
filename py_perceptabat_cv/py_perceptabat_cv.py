#!/usr/bin/env python

# Author: Aretas Gaspariunas 2019

import os
import subprocess
from threading import Thread
from typing import Dict, List, Optional
import shutil
import csv

def create_trans_dict(input_file: str) -> Dict:

    try:
        translation_dict = {}
        with open(input_file, 'r') as f:
            counter = 1
            for line in f:
                smiles, id_ = line.split()
                translation_dict[str(counter)] = id_
                counter += 1

        return translation_dict

    except FileNotFoundError:
        raise

def split_file(filepath: str, chunksize: int = 5000) -> None:

    with open(filepath, 'rb') as file_obj:

        line_count = 0
        file_count = 0

        dirname, filename = os.path.split(os.path.abspath(filepath))

        chunked_file_object = open(os.path.join(dirname, filename.split('.')[0]+'__chunk__'+
            str(file_count)+'.'+filename.split('.')[1]), "wb")
        for line in file_obj:
            chunked_file_object.write(line)
            line_count += 1
            if line_count == chunksize:
                chunked_file_object.close()
                file_count += 1
                line_count = 0
                chunked_file_object = open(os.path.join(dirname, filename.split('.')[0]+'__chunk__'+
                    str(file_count)+'.'+filename.split('.')[1]), "wb")

        chunked_file_object.close()

        if line_count == 0:
            os.remove(os.path.join(dirname, filename.split('.')[0]+'__chunk__'+
                str(file_count)+'.'+filename.split('.')[1]))

def run_cmd(add_flags: List[str] = [], verbose: bool = False, windows=False) -> None:

    cmd_list = ["perceptabat_cv"]
    if windows:
        cmd_list = ["perceptabat_cv.exe"]
    # adding user specified flags
    if add_flags:
        for i in add_flags:
            cmd_list.append(i)
    else:
        raise ValueError('No perceptabat_cv arguments provided.')

    if verbose is True:
        subprocess.Popen(cmd_list).wait()
    else:
        subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()

def parse_percepta_output(result_file: object, offset: int = 0) -> Dict:

    parsed_output = {}

    for line in result_file:

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

    return parsed_output

def parsing_chunks(chunk_dir_path: str, chunksize: int) -> Dict:

    # parsing chunks
    result_dict = {}
    for i in os.listdir(chunk_dir_path):
        if '__chunk__res' in i:

            chunk_no = int(i.split('__')[2].split('.')[0].strip('res'))

            with open(os.path.join(chunk_dir_path, i), 'r') as output_file:
                temp_result_dict = parse_percepta_output(output_file, offset=chunk_no*chunksize)
                result_dict.update(temp_result_dict)

        # remove chunk files
        if '__chunk__' in i:
            os.remove(os.path.join(chunk_dir_path, i))

    return result_dict

def write_csv(result_dict: Dict[str, Dict[str, str]], input_filepath: str = '',
    output_filepath: str = '') -> Dict:

    # creating missing keys
    acd_columns = []
    counter = 0
    for key, value in result_dict.items():
        for col, value1 in value.items():
            if col not in acd_columns:
                acd_columns.append(col)
        counter += 1
        if counter > 3000:
            break
    for key, value in result_dict.items():
        for col in acd_columns:
            if col not in value:
                result_dict[key][col] = 'NaN'

    # creating translation dictionary for IDs and checking input file
    translation_dict = create_trans_dict(input_filepath)
    # translating dict ids
    trans_result_dict = {}
    for cp_id, props in result_dict.items():
        trans_result_dict[translation_dict[cp_id]] = props

    # writting to csv
    acd_columns.append('compound_id')
    dirname, filename = os.path.split(os.path.abspath(input_filepath))
    with open(output_filepath, "w") as f:
        w = csv.DictWriter(f, acd_columns)
        w.writeheader()
        for k in trans_result_dict:
            w.writerow({col: trans_result_dict[k].get(col) or k for col in acd_columns})

    return trans_result_dict

def py_perceptabat_cv(percepta_cmd_str: str, threads: Optional[int] = None) -> Dict[str, Dict[str, str]]:

    # finding absolute paths for input
    input_filepath = [i for i in percepta_cmd_str.split() if '-' not in i][0]
    i_dirname, i_filename = os.path.split(os.path.abspath(input_filepath))
    percepta_cmd_str = percepta_cmd_str.replace(input_filepath, os.path.join(i_dirname, i_filename))
    input_filepath = os.path.join(i_dirname, i_filename)

    # absolute paths for output
    if 'TFNAME' not in percepta_cmd_str or '-R' in percepta_cmd_str or '-F' in percepta_cmd_str:
        raise ValueError('Input/outfile must be a .TXT file. .SDF and .RDF are not supported.')
    output_filepath = [i.split('TFNAME')[1] for i in percepta_cmd_str.split() if 'TFNAME' in i][0]
    o_dirname, o_filename = os.path.split(output_filepath)

    # use the same directory for output as input file
    percepta_cmd_str = percepta_cmd_str.replace(o_filename, os.path.join(i_dirname, o_filename))
    # argument sanity check
    if shutil.which('perceptabat_cv') is None:
        raise OSError('Failed to execute perceptabat_cv.')

    if not os.path.isfile(input_filepath):
        raise IOError('Failed to find input file.')

    if '__' in input_filepath or ' ' in input_filepath:
        raise ValueError("Please do not use '__' or space characters in input file name.")

    if isinstance(threads, int) and threads > 0 or threads is None:
        pass
    else:
        raise ValueError("Please use positive integer for threads argument.")

    with open(input_filepath) as f:
        num_lines = sum(1 for line in f) # counting number of lines in input file
        # testing the format of input file
        f.seek(0)
        for index, line in enumerate(f):
            if len(line.split(' ')) != 2:
                raise ValueError("Input file should contain two columns in format 'SMILES_col ID_col. Line: {0}".format(index))

    # setting number of threads to use
    if num_lines < 50:
        threads = 1
    elif threads is None:
        from multiprocessing import cpu_count
        threads = cpu_count()

    # split the input file into chunks
    chunksize = int(round(int(num_lines) / threads, 0))
    split_file(input_filepath, chunksize=chunksize)
    split_file_list = [i for i in os.listdir(i_dirname) if 'chunk' in i]

    # spawning threads
    th = []
    for index, file in enumerate(split_file_list):

        percepta_cmd_str_chunk = percepta_cmd_str.replace(i_filename, file).replace(
            o_filename, o_filename+'__chunk__res'+str(index))

        t = Thread(target=run_cmd, args=(percepta_cmd_str_chunk.split(), ))
        th.append(t)
        th[index].start()

    for t in th:
        t.join()

    # parsing chunks
    result_dict = parsing_chunks(i_dirname, chunksize)

    trans_result_dict = write_csv(result_dict, input_filepath=input_filepath,
        output_filepath=os.path.join(i_dirname, o_filename))

    return trans_result_dict

def main():

    import sys

    try:
        py_perceptabat_cv(' '.join([i for i in sys.argv[1:]]))
    except IndexError:
        print('Missing one or more arguments.')

if __name__ == "__main__":

    main()
