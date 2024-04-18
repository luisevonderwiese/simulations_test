import os
import json
from ete3 import Tree
from tabulate import tabulate
from lingdata.categorical import CategoricalData

msa_types = ["bin", "catg_bin", "catg_multi"]
msa_types = ["bin"]
file_ending = {"bin" : ".phy", "catg_bin" + ".catg", "catg_multi" + ".catg"}
msa_dir = "data/msa"
raxml_dir = "data/raxml-ng"
input_dir = "data/simulated_data"
reference_trees_dir = "data/networks"



def run_inference(msa_path, model, prefix, args = ""):
    if not os.path.isfile(msa_path):
        print("MSA " + msa_path + " does not exist")
        return
    prefix_dir = "/".join(prefix.split("/")[:-1])
    if not os.path.isdir(prefix_dir):
        os.makedirs(prefix_dir)
    if not os.path.isfile(best_tree_path(prefix)):
        args = args + " --redo"
    command = "./bin/raxml-ng"
    command += " --msa " + msa_path
    command += " --model " + model
    command += " --prefix " + prefix
    command += " --threads auto --seed 2"
    command += " " + args
    os.system(command)


def rf_distance(t1, t2):
    if t1 is None or t2 is None:
        return float('nan')
    if t1 != t1 or t2 != t2:
        return float("nan")
    rf, max_rf, common_leaves, parts_t1, parts_t2,discard_t1, discart_t2 = t1.robinson_foulds(t2, unrooted_trees = True)
    if max_rf == 0:
        return float('nan')
    return rf/max_rf * 100

def generate_msas():
    msa_dir = "data/msa"

    input_dir = "data/simulated_data"
    for borrowing_mode in os.listdir(input_dir):
        borrowing_dir = os.path.join(input_dir, borrowing_mode)
        max_values_dict = {}
        for input_file in os.listdir(borrowing_dir):
            cd = CategoricalData.from_warnow_file(os.path.join(borrowing_dir, input_file))
            current_dir = os.path.join(msa_dir, borrowing_mode, input_file.split('.')[0])
            if not os.path.isdir(current_dir):
                os.makedirs(current_dir)
            for msa_type in msa_types:
                msa_file_name = os.path.join(current_dir, msa_type + file_ending[msa_type])
                cd.write_msa(msa_file_name, msa_type)
            max_values_dict[input_file] = cd.max_values()
        max_values_path = os.path.join(msa_dir, borrowing_mode, "max_values.csv")
        json.dump(d, open(max_values_path,'w+'))


def run_raxml_ng():
    msa_dir = "data/msa"
    raxml_dir = "data/raxml-ng"
    input_dir = "data/simulated_data"
    for borrowing_mode in os.listdir(input_dir):
        borrowing_dir = os.path.join(input_dir, borrowing_mode)
        max_values_path = os.path.join(msa_dir, borrowing_mode, "max_values.csv")
        max_values_dict = json.load(open(max_values_path))
        for input_file in os.listdir(borrowing_dir):
            current_msa_dir = os.path.join(msa_dir, borrowing_mode, input_file.split('.')[0])
            msa_type = "bin"
            msa_file_name = os.path.join(current_msa_dir, msa_type + file_ending[msa_type])
            prefix = os.path.join(raxml_dir, borrowing_mode, input_file.split('.')[0], msa_type)
            run_inference(msa_file_name, "BIN+G", prefix)

            #msa_type = "catg_bin"
            #msa_file_name = os.path.join(current_msa_dir, msa_type + file_ending[msa_type])
            #prefix = os.path.join(raxml_dir, borrowing_mode, input_file.split('.')[0], msa_type)
            #run_inference(msa_file_name, "BIN+G", prefix, "--prob-msa on")

            #msa_type = "catg_multi"
            #msa_file_name = os.path.join(current_msa_dir, msa_type + file_ending[msa_type])
            #prefix = os.path.join(raxml_dir, borrowing_mode, input_file.split('.')[0], msa_type)
            #x = max_values_dict[input_file]
            #run_inference(msa_file_name, "MULTI" + str(x) + "_MK+G", prefix, "--prob-msa on")


def evaluate_trees():
    no_borrowing_trees = []
    with open("data/trees.txt") as trees_file:
        lines = trees_file.readlines()
    no_borrowing_trees = [Tree(line) for line in lines]
    results = [{} for _ in range(4)]
    for borrowing_mode in os.listdir(input_dir):
        poly_level = borrowing_mode,split("_")[0]
        for i in range(4):
            if poly_level not in results[i]:
                results[i][poly_level] = dict([(msa_type, []) for msa_type in msa_types])
        borrowing_dir = os.path.join(input_dir, borrowing_mode)
        max_values_path = os.path.join(msa_dir, borrowing_mode, "max_values.csv")
        max_values_dict = json.load(open(max_values_path))
        for input_file in os.listdir(borrowing_dir):
            if borrowing_mode,split("_")[1] == "noborrowing":
                idx = int(input_file.split("_")[1].split("tree")[0]) - 1
                reference_tree = no_borrowing_trees[idx]
                borrowing_edges = 0
            else:
                tree_name = input_file.split("_")[1] + ".txt"
                reference_tree = Tree(os.path.join(reference_trees_dir, tree_name))
                borrowing_edges = int(input_file.split("_")[1].split("-")[0].split("net")[0])
            for msa_type in msa_types:
                prefix = os.path.join(raxml_dir, borrowing_mode, input_file.split('.')[0], msa_type)
                ml_trees_path = prefix + ".raxml.mlTrees"
                if not os.path.isfile(ml_trees_path):
                    print("No results for", input_file, msa_type)
                    continue
                with open(ml_trees_path) as trees_file:
                    lines = trees_file.readlines()
                ml_trees = [Tree(line) for line in lines]
                rf_distances = [rf_distance(ml_tree, reference_tree) for ml_tree in ml_trees]
                results[borrowing_edges][poly_level][msa_type].append(sum(rf_distances) / len(rf_distances))

    headers = []"poly_level"] + msa_types
    for borrowing_edges in range(4):
        r = []
        for poly_level in results[borrowing_edges]:
            row = [poly_level]
            for msa_type in results[borrowing_edges][poly_level]:
                vec = results[borrowing_edges][poly_level][msa_type]
                row.append(sum(vec)/len(vec))
            r.append(row)
        print("Borrowing edges:", str(borrowing_edges))
        print(tabulate(r, tablefmt="pipe", headers = headers))
