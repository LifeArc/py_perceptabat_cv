#!/usr/bin/env python

# Author: Aretas Gaspariunas

from pathlib import Path
from typing import Dict, List, Optional, TextIO
import shutil
from tempfile import NamedTemporaryFile
from multiprocessing import cpu_count
import threading
import subprocess
import csv


def split_file(filepath: Path, num_lines: int, chunk_line_count: int = 5000) -> Dict[int, str]:

    """
    Splits a file into smaller chunks based on line count.
    Default maximum chunk line count is 5000 lines.
    Returns a dictionary of chunk paths.
    """

    line_count = 0
    file_count = 0
    final_line_count = 0
    chunk_path_dict = {}

    dirname = filepath.resolve().parent

    chunk_temp_file = NamedTemporaryFile(delete=False, suffix=".smi", dir=dirname)
    with open(filepath.resolve(), "rb") as f:
        for line in f:
            chunk_temp_file.write(line)
            line_count += 1
            final_line_count += 1

            if line_count == chunk_line_count or final_line_count == num_lines:

                chunk_path_dict[file_count] = chunk_temp_file.name
                file_count += 1
                line_count = 0
                chunk_temp_file.close()

                chunk_temp_file = NamedTemporaryFile(
                    delete=False, suffix=".smi", dir=dirname
                )

    chunk_temp_file.close()

    if line_count == 0:
        Path(chunk_temp_file.name).unlink()

    return chunk_path_dict


def run_cmd(flag_list: List[str] = [], verbose: bool = False) -> None:

    """
    Runs perceptabat_cv with input from flag_list.
    Set verbose to True for console messages from perceptabat_cv.
    """

    if not flag_list:
        raise ValueError("No perceptabat_cv arguments provided")
    else:
        cmd_list = flag_list.copy()
        cmd_list.insert(0, "perceptabat_cv")

    output = subprocess.run(
        cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout

    if verbose or b"Total structures: 1       Processed: 1" not in output:
        print(output.decode("utf-8"))


def parse_percepta_txt_output(
    result_file: TextIO, offset: int = 0
) -> Dict[str, Dict[str, str]]:

    """
    Parses text output file from perceptabat_cv.
    Returns a nested dictionary {compound ID: {property name: value}}.
    """

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


def parse_chunks(
    output_chunk_path_dict: Dict[int, str], chunk_line_count: int
) -> Dict[str, Dict[str, str]]:

    """
    Iterates and parses a dictionary of output file paths.
    Returns a dictionary of results.
    """

    result_dict = {}

    for chunk_no, chunk in output_chunk_path_dict.items():
        with open(chunk, "r") as output_file:
            temp_result_dict = parse_percepta_txt_output(
                output_file, offset=chunk_no * chunk_line_count
            )
            result_dict.update(temp_result_dict)

    return result_dict


def write_results(
    result_dict: Dict[str, Dict[str, str]],
    trans_dict: Dict[str, str],
    input_filepath: Path,
    output_filepath: Path,
    write_csv: Optional[bool] = False,
) -> Dict[str, Dict[str, str]]:

    """
    Returns processed output by combining results_dict (predicted values) and trans_dict (compound IDs).
    Optionally writes results to a CSV file.
    """

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
    if write_csv is True:
        acd_columns.append("compound_id")
        with open(output_filepath, "w") as f:
            w = csv.DictWriter(f, acd_columns)
            w.writeheader()
            for k in trans_result_dict:
                w.writerow(
                    {col: trans_result_dict[k].get(col) or k for col in acd_columns}
                )

    return trans_result_dict


def parse_input_string(percepta_cmd_str: str) -> tuple:

    """
    Parses input command string and writes a new version with absolute paths.
    """

    input_filepath = Path([i for i in percepta_cmd_str.split() if "-" not in i][0])
    abs_input_filepath = input_filepath.resolve()
    percepta_cmd_str = percepta_cmd_str.replace(
        str(input_filepath), str(abs_input_filepath)
    )

    output_filepath = Path([
        i.split("TFNAME")[1] for i in percepta_cmd_str.split() if "TFNAME" in i
    ][0])
    percepta_cmd_str = percepta_cmd_str.replace(
        str(output_filepath.name), str(abs_input_filepath.parent / output_filepath.name)
    )

    return (
        abs_input_filepath.parent,
        abs_input_filepath.name,
        abs_input_filepath,
        output_filepath,
        output_filepath.parent,
        output_filepath.name,
        percepta_cmd_str,
    )


def sanity_check(percepta_cmd_str: str, abs_input_filepath: Path, threads: int) -> None:

    """
    Checks for sanity.
    """

    if shutil.which("perceptabat_cv") is None:
        raise OSError("perceptabat_cv executable not found")

    if (
        "TFNAME" not in percepta_cmd_str
        or "-R" in percepta_cmd_str
        or "-F" in percepta_cmd_str
    ):
        raise ValueError(
            "Input/output file must be a TXT file. SDF and RDF extensions are not supported"
        )

    if not abs_input_filepath.is_file():
        raise FileNotFoundError("Failed to find input file")

    if not str(abs_input_filepath).lower().endswith(".smi"):
        raise ValueError("Input file must have .smi extension")

    if not (isinstance(threads, int) and threads > 0 or threads is None):
        raise ValueError("Please use a positive integer for threads argument")


def py_perceptabat_cv(
    percepta_cmd_str: str,
    threads: Optional[int] = None,
    write_csv: Optional[bool] = False,
) -> Dict[str, Dict[str, str]]:

    """
    Python wrapper for perceptabat_cv with parallel processing support.
    Accepts perceptabat_cv options as a Python string.

    Parameters
    ----------
    percepta_cmd_string : string
        perceptabat_cv options as a Python string.
    threads : integer, default None
        Number of threads to use. Default is to automatically detect an optimal number of threads to use.
    write_csv : bool, default False
         Set to True to write output to CSV file.

    Returns
    -------
    Dictionary
        Calculated properties for input compounds.

    Examples
    --------
    Calculating properties with defaults.
    >>> input_filename = 'my_compounds.smi'
    >>> output_filename = 'my_output.csv'
    >>> command_string = f"-MLOGP -OLOGPALGA -TLOGP -TFNAME{output_filename} {input_filename}"
    >>> results = py_perceptabat_cv(percepta_cmd_string)
    >>> results
        {'benzene': {'acd_logp': '2.041', 'acd_logp_error': '0.00', 'acd_logp_old': '2.041+/-0.000'},
        'phenol': {'acd_logp': '1.628', 'acd_logp_error': '0.00', 'acd_logp_old': '1.628+/-0.000'}}
    """

    (
        i_dirname,
        i_filename,
        abs_input_filepath,
        output_filepath,
        o_dirname,
        o_filename,
        percepta_cmd_str,
    ) = parse_input_string(percepta_cmd_str)

    sanity_check(percepta_cmd_str, abs_input_filepath, threads)

    # creating translation dictionary for IDs and checking input file formatting
    try:
        translation_dict = {}
        num_lines = 0  # counting number of lines in input file
        with open(abs_input_filepath, "r") as f:
            for l in f:
                if (
                    len(l.split(" ")) != 2
                ):  # checking the format of input file; does not check for SMILES validity
                    raise ValueError(
                        f"Input file should contain two columns separated by a space in a format:"
                        " 'SMILES_col ID_col'. Line: {num_lines}"
                    )
                smiles, id_ = l.split()
                num_lines += 1
                translation_dict[str(num_lines)] = id_
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
    chunk_line_count = int(round(int(num_lines) / threads, 0))
    chunk_path_dict = split_file(abs_input_filepath, num_lines, chunk_line_count=chunk_line_count)
    output_chunk_path_dict = {}

    try:
        for chunk_no, chunk in chunk_path_dict.items():

            input_chunk_name = Path(chunk).name
            output_chunk_name = o_filename + "_result_" + str(chunk_no)
            output_chunk_path_dict[chunk_no] = i_dirname / output_chunk_name

            percepta_cmd_str_chunk = percepta_cmd_str.replace(
                i_filename, input_chunk_name
            ).replace(o_filename, output_chunk_name)

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
        result_dict = parse_chunks(output_chunk_path_dict, chunk_line_count)

        # adding back original IDs and writting csv
        trans_result_dict = write_results(
            result_dict,
            translation_dict,
            abs_input_filepath,
            i_dirname / o_filename, # output_filepath,
            write_csv=write_csv,
        )
    except Exception:
        raise
    finally:
        for i in list(chunk_path_dict.values()) + list(output_chunk_path_dict.values()):
            Path(i).unlink()

    return trans_result_dict


def perceptabat_api(
    compound_dict: Dict[str, str],
    properties: Optional[List[str]] = ["logp", "pka", "logd", "sigma"],
    param: Optional[Dict[str, str]] = {
        "logp_algorithm": "consensus",
        "pka_algorithm": "classic",
        "logd_ph": "7.4",
    },
) -> Dict[str, Dict[str, str]]:

    """
    Python API for py_perceptabat_cv.

    Parameters
    ----------
    compound_dict : dictionary
        Compound dictionary to calculate properties for. Keys for compound ID and values for Daylight SMILES.
    properties : list, default ["logp", "pka", "logd", "sigma"]
        List properties to calculate. Default to calculate all. Calculations are limited to default value.
        Please use py_perceptabat_cv() if you wish to calculate any other properties.
    param : dictionary, default {"logp_algorithm": "consensus", "pka_algorithm": "classic", "logd_ph": "7.4"}
         Parameters for calculations.

    Returns
    -------
    Dictionary
        Calculated properties for input compounds.

    Examples
    --------
    Calculating properties with defaults.
    >>> d = {'benzene': 'c1ccccc1', 'phenol': 'c1ccc(cc1)O'}
    >>> results = perceptabat_api(d)
    >>> results
    {'benzene': {'acd_mv': '89.434', 'acd_mr': '26.253', 'acd_logp': '2.041', 'acd_logp_error': '0.00', 'acd_logp_old':
        '2.041+/-0.000', 'acd_ruleof5_hdonors': '0', 'acd_ruleof5_hacceptors': '0', 'acd_ruleof5_frb': '0', 'acd_ruleof5_mw':
        '78.112', 'acd_ruleof5_psa': '0.000', 'acd_ruleof5_psanobis': '0.000', 'acd_ruleof5': '0', 'acd_logd_ph': '7.40',
        'acd_logd': '2.041', 'acd_pka_caution_apparent': 'The structure does not contain ionization centers calculated by current version of ACD/pKa',
        'acd_pka_ionicform_apparent': 'NaN', 'acd_pka_acidic_apparent_1': 'NaN', 'acd_pka_acidic_error_apparent_1': 'NaN',
        'acd_pka_acidic_dissatom_apparent_1': 'NaN', 'acd_pka_acidic_disstype_apparent_1': 'NaN', 'acd_pka_acidic_equation_apparent_1': 'NaN',
        'acd_pka_acidic_all_apparent_1': 'NaN'},
        'phenol': {'acd_mv': '87.863', 'acd_mr': '28.134', 'acd_logp': '1.628', 'acd_logp_error': '0.00', 'acd_logp_old': '1.628+/-0.000',
        'acd_ruleof5_hdonors': '1', 'acd_ruleof5_hacceptors': '1', 'acd_ruleof5_frb': '0', 'acd_ruleof5_mw': '94.111',
        'acd_ruleof5_psa': '20.230', 'acd_ruleof5_psanobis': '20.230', 'acd_ruleof5': '0', 'acd_logd_ph': '7.40', 'acd_logd': '1.626',
        'acd_pka_ionicform_apparent': 'HL', 'acd_pka_acidic_apparent_1': '9.862', 'acd_pka_acidic_error_apparent_1': '0.13',
        'acd_pka_acidic_dissatom_apparent_1': '7', 'acd_pka_acidic_disstype_apparent_1': 'MA', 'acd_pka_acidic_equation_apparent_1': 'HL/H+L',
        'acd_pka_acidic_all_apparent_1': 'pKa(HL/H+L; 7) = 9.86+/-0.13', 'acd_pka_caution_apparent': 'NaN'}}
    """

    logp_param_conversion = {"consensus": "CONSENSUS", "galas": "GALAS", "classic": "A"}
    pka_param_conversion = {"galas": "GALAS", "classic": ""}
    logd_param_conversion = {
        "consensus_galas": "CONSGALAS",
        "consensus_classic": "CONSCLASS",
        "galas_galas": "GALAS",
        "galas_classic": "GALASCLASS",
        "classic_galas": "CLASSGALAS",
        "classic_classic": "CLASS",
    }

    if 'logd_ph' not in param:
        param['logd_ph'] = '7.4'
    if 'logp_algorithm' not in param:
        param['logp_algorithm'] = 'consensus'
    if 'pka_algorithm' not in param:
        param['pka_algorithm'] = 'classic'

    prop_conversion = {
        "logp": f"-MLOGP -TLOGP -OLOGPALG{logp_param_conversion[param['logp_algorithm']]} -OLOGPRULE5FULL -OLOGPRULE5FRB -OLOGPRULE5PSA",
        "pka": f"-MPKAAPP{pka_param_conversion[param['pka_algorithm']]} -TPKA -OPKAMOST -OOUTSPLITACIDBASIC",
        "logd": f"-MLOGD -TLOGD -OLOGDPH1{param['logd_ph']} -OLOGDALG{logd_param_conversion[param['logp_algorithm'] + '_' + param['pka_algorithm']]}",
        "sigma": "-MSIGMA -TSIGMA",
    }

    cmd_string = "-OOVERWRITE "
    for prop in properties:
        cmd_string += prop_conversion[prop] + " "

    with NamedTemporaryFile(delete=True, suffix=".smi", mode="w+t") as f:
        writer = csv.writer(f, delimiter=" ")
        for key, value in compound_dict.items():
            writer.writerow([value, key])
        f.flush()

        cmd_string += f"-TFNAMEoutput.csv {f.name}"

        return py_perceptabat_cv(cmd_string)


def main():

    import sys

    try:
        if sys.argv[1] in ("-H", "-h"):
            run_cmd(flag_list=["-H"], verbose=True)
        else:
            py_perceptabat_cv(" ".join([i for i in sys.argv[1:]]), write_csv=True)
    except IndexError:
        print("Missing one or more arguments")


if __name__ == "__main__":

    main()
