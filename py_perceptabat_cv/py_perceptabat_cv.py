#!/usr/bin/env python

# Author: Aretas Gaspariunas

import os
from typing import Dict, List, Optional
import shutil
import tempfile
from multiprocessing import cpu_count
import threading
import subprocess
import csv


def split_file(filepath: str, chunksize: int = 5000) -> None:

    line_count = 0
    file_count = 0

    dirname, filename = os.path.split(os.path.abspath(filepath))

    chunk_temp_file = tempfile.NamedTemporaryFile(
        delete=False, prefix=str(file_count) + "__chunk__", suffix=".smi", dir=dirname
    )

    for line in (line for line in open(filepath, "rb")):
        chunk_temp_file.write(line)
        line_count += 1
        if line_count == chunksize:

            chunk_temp_file.close()
            file_count += 1
            line_count = 0

            chunk_temp_file = tempfile.NamedTemporaryFile(
                delete=False, prefix=str(file_count) + "__chunk__", suffix=".smi", dir=dirname
            )

    chunk_temp_file.close()

    if line_count == 0:
        os.remove(os.path.abspath(chunk_temp_file.name))


def run_cmd(flag_list: List[str] = [], verbose: bool = False) -> None:

    if not flag_list:
        raise ValueError("No perceptabat_cv arguments provided.")
    else:
        cmd_list = flag_list.copy()
        cmd_list.insert(0, "perceptabat_cv")

    output = subprocess.run(
        cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout

    if verbose or b"Total structures: 1       Processed: 1" not in output:
        print(output.decode("utf-8"))


def parse_percepta_output(
    result_file: object, offset: int = 0
) -> Dict[str, Dict[str, str]]:

    parsed_output = {}

    for line in result_file:
        if line.split()[0].isdigit() and line.split()[1] != "ID:":
            cp_id = str(int(line.split()[0]) + offset)
            col_name = line.split()[1].rstrip(":").lower()
            value = line.split(": ")[1].rstrip("\n")
            if not cp_id in parsed_output:
                parsed_output[cp_id] = {}
            parsed_output[cp_id][col_name] = value
        else:
            continue

    return parsed_output


def parse_chunks(chunk_dir_path: str, chunksize: int) -> Dict[str, Dict[str, str]]:

    # parsing chunks
    result_dict = {}
    for i in os.listdir(chunk_dir_path):
        if "__chunk__res" in i:
            chunk_no = int(i.split("__chunk__result")[1])
            output_file = (line for line in open(os.path.join(chunk_dir_path, i), "r"))
            temp_result_dict = parse_percepta_output(
                output_file, offset=chunk_no * chunksize
            )
            result_dict.update(temp_result_dict)
        # remove input and output chunk files
        if "__chunk__" in i:
            os.remove(os.path.join(chunk_dir_path, i))

    return result_dict


def write_csv(
    result_dict: Dict[str, Dict[str, str]],
    trans_dict: Dict[str, str],
    input_filepath: str = "",
    output_filepath: str = "",
) -> Dict[str, Dict[str, str]]:

    # obtaining all possible column names
    acd_columns = []
    counter = 0
    for key, value in result_dict.items():
        for col, value1 in value.items():
            if col not in acd_columns:
                acd_columns.append(col)
        counter += 1
        if counter == 10 ** 4:
            break

    # filling in missing columns
    for key, value in result_dict.items():
        for col in acd_columns:
            if col not in value:
                result_dict[key][col] = "NaN"

    # translating ID back to original IDs as provided in input file
    trans_result_dict = {}
    for cp_id, props in result_dict.items():
        trans_result_dict[trans_dict[cp_id]] = props

    # writting to csv
    acd_columns.append("compound_id")
    with open(output_filepath, "w") as f:
        w = csv.DictWriter(f, acd_columns)
        w.writeheader()
        for k in trans_result_dict:
            w.writerow({col: trans_result_dict[k].get(col) or k for col in acd_columns})

    return trans_result_dict


def py_perceptabat_cv(
    percepta_cmd_str: str, threads: Optional[int] = None
) -> Dict[str, Dict[str, str]]:

    input_filepath = [i for i in percepta_cmd_str.split() if "-" not in i][0]
    i_dirname, i_filename = os.path.split(os.path.abspath(input_filepath))
    percepta_cmd_str = percepta_cmd_str.replace(
        input_filepath, os.path.join(i_dirname, i_filename)
    )
    abs_input_filepath = os.path.join(i_dirname, i_filename)

    # absolute paths for output
    output_filepath = [
        i.split("TFNAME")[1] for i in percepta_cmd_str.split() if "TFNAME" in i
    ][0]
    o_dirname, o_filename = os.path.split(output_filepath)
    percepta_cmd_str = percepta_cmd_str.replace(
        o_filename, os.path.join(i_dirname, o_filename)
    )

    # argument sanity check
    if shutil.which("perceptabat_cv") is None:
        raise OSError("perceptabat_cv executable is not found.")

    if (
        "TFNAME" not in percepta_cmd_str
        or "-R" in percepta_cmd_str
        or "-F" in percepta_cmd_str
    ):
        raise ValueError(
            "Input/output file must be a .TXT file. .SDF and .RDF extensions are not supported."
        )

    if not os.path.isfile(abs_input_filepath):
        raise FileNotFoundError("Failed to find input file.")

    if not i_filename.lower().endswith(".smi"):
        raise ValueError("Input file must have .smi extension")

    if "__" in i_filename or " " in i_filename or "chunk" in i_filename:
        raise ValueError(
            "Please do not use '__' or space or 'chunk' characters/words in input file name."
        )

    if isinstance(threads, int) and threads > 0 or threads is None:
        pass
    else:
        raise ValueError("Please use positive integer for threads argument.")

    # creating translation dictionary for IDs and checking input file
    try:
        translation_dict = {}
        num_lines = 1  # counting number of lines in input file
        for l in (line for line in open(abs_input_filepath, "r")):
            if (
                len(l.split(" ")) != 2
            ):  # checking the format of input file; does not check for SMILES validity
                raise ValueError(
                    "Input file should contain two columns in format:"
                    " 'SMILES_col ID_col'. Line: {0}".format(num_lines)
                )
            smiles, id_ = l.split()
            translation_dict[str(num_lines)] = id_
            num_lines += 1
    except IOError:
        raise

    # setting number of threads to use
    if threads is None:
        threads = 1
        for cores in [core for core in range(1, cpu_count() + 1)][::-1]:
            if num_lines / cores > 50:
                threads = cores
                break

    # split the input file into chunks
    chunksize = int(round(int(num_lines) / threads, 0))
    split_file(abs_input_filepath, chunksize=chunksize)
    split_file_list = [i for i in os.listdir(i_dirname) if "chunk" in i]

    try:
        # spawning threads
        for chunk in split_file_list:
            chunk_no = int(chunk.split("__chunk__")[0])
            percepta_cmd_str_chunk = percepta_cmd_str.replace(
                i_filename, chunk
            ).replace(o_filename, o_filename + "__chunk__result" + str(chunk_no))
            t = threading.Thread(target=run_cmd, args=(percepta_cmd_str_chunk.split(),))
            t.daemon = True
            t.start()

        # waiting for threads to finish
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()

        # parsing chunks
        result_dict = parse_chunks(i_dirname, chunksize)

        # adding back original IDs and writting to csv
        trans_result_dict = write_csv(
            result_dict,
            translation_dict,
            input_filepath=abs_input_filepath,
            output_filepath=os.path.join(i_dirname, o_filename),
        )
    except Exception as e:
        # remove chunk files
        for i in os.listdir(i_dirname):
            if "__chunk__" in i:
                os.remove(os.path.join(i_dirname, i))
        print(e)

    return trans_result_dict


def main():

    import sys

    try:
        py_perceptabat_cv(" ".join([i for i in sys.argv[1:]]))
    except IndexError:
        print("Missing one or more arguments.")


if __name__ == "__main__":

    main()
