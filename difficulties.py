import os
import json
from ete3 import Tree
from tabulate import tabulate
from lingdata.categorical import CategoricalData
import pythia

msa_dir = "data/msa"
pythia_dir = "data/pythia"




def run_pythia():
    for borrowing_mode in os.listdir(input_dir):
        borrowing_dir = os.path.join(input_dir, borrowing_mode)
        max_values_path = os.path.join(msa_dir, borrowing_mode, "max_values.csv")
        max_values_dict = json.load(open(max_values_path))
        for input_file in os.listdir(borrowing_dir):
            msa_path = os.path.join(msa_dir, borrowing_mode, input_file.split('.')[0], "bin.phy")
            prefix = os.path.join(pythia_dir, borrowing_mode, input_file.split('.')[0], "bin")
            pythia.run_with_padding(msa_path, prefix)


def evaluate():
    results = [{} for _ in range(4)]
    for borrowing_mode in os.listdir(input_dir):
        poly_level = borrowing_mode.split("_")[0]
        for i in range(4):
            if poly_level not in results[i]:
                results[i][poly_level] = []
        borrowing_dir = os.path.join(input_dir, borrowing_mode)
        for input_file in os.listdir(borrowing_dir):
            if borrowing_mode.split("_")[1] == "noborrowing":
                borrowing_edges = 0
            else:
                borrowing_edges = int(input_file.split("_")[1].split("-")[0].split("net")[1])
            prefix = os.path.join(pythia_dir, borrowing_mode, input_file.split('.')[0], "bin")
            results[borrowing_edges][poly_level][msa_type].append(pythia.get_difficulty(prefix))

    headers = ["poly_level"] + [i in range(4)]
    r = []
    for borrowing_edges in range(4):
        for poly_level in results[borrowing_edges]:
            row = [poly_level]
            vec = results[borrowing_edges][poly_level]
            row.append(sum(vec)/len(vec))
        r.append(row)
    print(tabulate(r, tablefmt="pipe", headers = headers))


run_pythia()
evaluate()
