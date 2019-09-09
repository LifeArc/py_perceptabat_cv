#!/usr/bin/env python

# Author: Aretas Gaspariunas

import os
from typing import Dict, List, Optional
import shutil
import threading
import subprocess
import csv

def split_file(filepath: str, chunksize: int = 5000) -> None:

    line_count = 0
    file_count = 0

    dirname, filename = os.path.split(os.path.abspath(filepath))

    chunked_file_object = open(os.path.join(dirname, filename.split('.')[0]+'__chunk__'+
        str(file_count)+'.'+filename.split('.')[1]), "wb")
    for line in (line for line in open(filepath, 'rb')):
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

def run_cmd(add_flags: List[str] = [], verbose: bool = False) -> None:

    cmd_list = ["perceptabat_cv"]

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
        if line.split()[0].isdigit() and line.split()[1] != 'ID:':
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
            output_file = (line for line in open(os.path.join(chunk_dir_path, i), 'r'))
            temp_result_dict = parse_percepta_output(output_file, offset=chunk_no*chunksize)
            result_dict.update(temp_result_dict)
        # remove chunk files
        if '__chunk__' in i:
            os.remove(os.path.join(chunk_dir_path, i))

    return result_dict

def write_csv(result_dict: Dict[str, Dict[str, str]], trans_dict: Dict[str, str],
    input_filepath: str = '', output_filepath: str = '') -> Dict:

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

    # translating dict ids
    trans_result_dict = {}
    for cp_id, props in result_dict.items():
        trans_result_dict[trans_dict[cp_id]] = props

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
    output_filepath = [i.split('TFNAME')[1] for i in percepta_cmd_str.split() if 'TFNAME' in i][0]
    o_dirname, o_filename = os.path.split(output_filepath)
    percepta_cmd_str = percepta_cmd_str.replace(o_filename, os.path.join(i_dirname, o_filename))

    # argument sanity check
    if shutil.which('perceptabat_cv') is None:
        raise OSError('Failed to execute perceptabat_cv.')

    if 'TFNAME' not in percepta_cmd_str or '-R' in percepta_cmd_str or '-F' in percepta_cmd_str:
        raise ValueError('Input/output file must be a .TXT file. .SDF and .RDF are not supported.')

    if '__' in input_filepath or ' ' in input_filepath or 'chunk' in input_filepath:
        raise ValueError("Please do not use '__' or space characters in input file name.")

    if not os.path.isfile(input_filepath):
        raise IOError('Failed to find input file.')

    if isinstance(threads, int) and threads > 0 or threads is None:
        pass
    else:
        raise ValueError("Please use positive integer for threads argument.")

    # creating translation dictionary for IDs and checking input file
    try:
        translation_dict = {}
        num_lines = 1 # counting number of lines in input file
        for l in (line for line in open(input_filepath, 'r')):
            if len(l.split(' ')) != 2: # checking the format of input file
                raise ValueError("Input file should contain two columns in format:"
                    " 'SMILES_col ID_col'. Line: {0}".format(num_lines))
            smiles, id_ = l.split()
            translation_dict[str(num_lines)] = id_
            num_lines += 1
    except FileNotFoundError:
        raise

    # setting number of threads to use
    if threads is None:
        from multiprocessing import cpu_count
        threads = 1
        for i in [i for i in range(1, cpu_count()+1)][::-1]:
            if num_lines / i > 50:
                threads = i
                break

    # split the input file into chunks
    chunksize = int(round(int(num_lines) / threads, 0))
    split_file(input_filepath, chunksize=chunksize)
    split_file_list = [i for i in os.listdir(i_dirname) if 'chunk' in i]

    # spawning threads
    for index, chunk in enumerate(split_file_list):
        percepta_cmd_str_chunk = percepta_cmd_str.replace(i_filename, chunk).replace(
            o_filename, o_filename+'__chunk__res'+str(index))
        t = threading.Thread(target=run_cmd, args=(percepta_cmd_str_chunk.split(), ))
        t.daemon = True
        t.start()

    main_thread = threading.currentThread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()

    # parsing chunks
    result_dict = parsing_chunks(i_dirname, chunksize)

    trans_result_dict = write_csv(result_dict, translation_dict, input_filepath=input_filepath,
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
