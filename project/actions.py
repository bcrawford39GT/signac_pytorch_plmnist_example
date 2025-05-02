"""Basic example of a signac project using row for job submissions."""
# actions.py

import argparse
import os
import warnings
import signac
import shutil
import subprocess

import json, datetime
from pathlib import Path

from signac import get_project
from signac.job import Job

from src.seed_analysis import seed_analysis

# ******************************************************
# NOTES (START)
# ******************************************************

# Set the walltime, memory, and number of CPUs and GPUs needed
# for each individual job, based on the part/section.
# *******************************************************
# *******************   WARNING   ***********************
# It is recommended to check all HPC submisstions with the
# '--dry-run' (i.e., 'row submit --dry-run') command so you 
# do not make an errors requesting the CPUs, GPUs, and 
# other parameters by its value that many cause more 
# resources to be used than expected, which may result in 
# higher HPC or cloud computing costs! 
# *******************   WARNING   ***********************
# *******************************************************

# ******************************************************
# NOTES (END)
# ******************************************************


# SET THE PROJECTS DEFAULT DIRECTORY AND PATHS
signac_directory = Path.cwd()

if signac_directory.name != "project":
    raise ValueError(f"Please run this script from inside the `project` directory.")

data_directory = signac_directory.parent / "data"
analysis_directory = signac_directory / "analysis"
output_file = analysis_directory / "output.txt"

# ┌─────────────────────────────────┐
# │ Part 1 - write the job document │
# └─────────────────────────────────┘

def part_1_initialize_signac_command(*jobs):
    """Set the system's job parameters in the json file."""

    for job in jobs:
        output_file.unlink(missing_ok=True)

        # here we write "signac_job_document.json" file.
        # signac takes care of the writing - we just add attributes to job.document
        # note that this file isn't used by the project - it's just here for demonstration.

        # note that we can access the statepoint variables (from init.py) via job.statepoint
        job.document.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        job.document.seed = job.statepoint.seed_int


# ┌──────────────────────────────────┐
# │ Part 2 - download the MNIST data │
# └──────────────────────────────────┘

# operation: download the data
def part_2_download_data_command(*jobs):
    """Download the data."""

    print(f"data_directory = {data_directory}")
    # Make the directory
    if not (data_directory / "MNIST").exists():
        data_directory.mkdir(parents=True, exist_ok=True)

        print(f"python -m plmnist.download --data_dir data_directory = python -m plmnist.download --data_dir {data_directory}")
        # Download the data
        exec_download_data = subprocess.Popen(
            f"python -m plmnist.download --data_dir {data_directory}", 
            shell=True, 
            stderr=subprocess.STDOUT
        )
        os.wait4(exec_download_data.pid, os.WSTOPPED)

    for job in jobs:
        # Check that data has been downloaded and create completion files 
        # in each state point directory.
        if (data_directory / "MNIST").exists():
            # Print completion file
            exec_make_completion_file = subprocess.Popen(
                f"touch {job.fn('data_download_complete.txt')}",
                shell=True, 
                stderr=subprocess.STDOUT
            )
            os.wait4(exec_make_completion_file.pid, os.WSTOPPED)


# ┌──────────────────────────────────────┐
# │ Part 3 - train and test a neural net │
# └──────────────────────────────────────┘

def part_3_train_and_test_command(*jobs):
    """Run the train + test command."""

    # The below will output the 'results.json' file
    for job in jobs:
        output_file.unlink(missing_ok=True)

        train_command =  (
            f"python -m plmnist "
            f"--num_epochs {int(job.statepoint.num_epochs_int)} "
            f"--log_path {job.path} "
            f"--result_path {job.path} "
            f"--data_dir {data_directory} "
            f"--batch_size {int(job.statepoint.batch_size_int)} "
            f"--hidden_size {int(job.statepoint.hidden_size_int)} "
            f"--learning_rate {float(job.statepoint.learning_rate_float)} "
            f"--dropout_prob {float(job.statepoint.dropout_prob_float)} "
            f"--seed {int(job.statepoint.seed_int)} "
            f"--fgsm_epsilon {float(job.statepoint.fgsm_epsilon_float)} "
            f"--no_dhash "
            f"--no_fgsm "
        )

        print(f"Running training/testing for {job}")
        exec_make_completion_file = subprocess.Popen(
                train_command,
                shell=True, 
                stderr=subprocess.STDOUT
            )
        os.wait4(exec_make_completion_file.pid, os.WSTOPPED)
        

# ┌──────────────────────────────┐
# │ Part 4 - run the FGSM attack │
# └──────────────────────────────┘

def part_4_fgsm_attack_command(*jobs: Job):
    """Run FGSM attack command."""

    for jobs in Job:
        output_file.unlink(missing_ok=True)

        fgsm_attack_command =  (
            f"python -m plmnist.fgsm "
            f"--seed {int(job.statepoint.seed_int)} "
            f"--result_path {job.path} "
            f"--fgsm_epsilon {float(job.statepoint.fgsm_epsilon_float)} "
        )

        print(f"Running fgsm for {job}")
        exec_make_completion_file = subprocess.Popen(
                fgsm_attack_command,
                shell=True, 
                stderr=subprocess.STDOUT
            )
        os.wait4(exec_make_completion_file.pid, os.WSTOPPED)

        # Check if the training, testing, and writing and completed properly.
        passing_check_list = []
        if job.isfile("results.json"):
            with open(job.fn("results.json"), "r") as json_log_file:
                try:
                    loaded_json_file = json.load(json_log_file)
                except json.decoder.JSONDecodeError:
                    passing_check_list.append(False)

                for key in ["fgsm", "test_loss", "test_acc"]:
                    if key not in loaded_json_file:
                        passing_check_list.append(False)
                    elif key == "fgsm":
                        if "accuracy" not in loaded_json_file["fgsm"]:
                            passing_check_list.append(False)

        print(f'passing_check_list = {passing_check_list}')

        # Print completion file if completed correcty.
        if False not in passing_check_list:
            # Print completion file
            exec_make_completion_file = subprocess.Popen(
                f"touch {job.fn('fgsm_attack_complete.txt')}",
                shell=True, 
                stderr=subprocess.STDOUT
            )
            os.wait4(exec_make_completion_file.pid, os.WSTOPPED)


# ┌─────────────────────────────────────┐
# │ Part 5 - compute avg/std over seeds │
# └─────────────────────────────────────┘

# Note: Brad note: not sure if this is correct... need to check.

def part_5_seed_analysis_command(*aggregated_jobs: Job):
    """Write the output file with the seed averages."""

    print(f"analysis_directory = {analysis_directory}")
    if not os.path.isdir(analysis_directory):
        os.system(f"mkdir {analysis_directory}")

    seed_analysis(aggregated_jobs, output_file)

    #Check that the replicate (seed) average file has been written and completed properly.
    passing_check_list = []
    if not output_file.exists():
        passing_check_list.append(False)

    with open(output_file, "r") as f:
        lines = f.readlines()

    project = get_project()

    num_seeds = set()
    for job in project:
        num_seeds.add(job.statepoint.seed_int)

    num_agg = len(project) / len(num_seeds)

    if len(lines) != num_agg + 1:
        passing_check_list.append(False)

    # Print completion file if completed correcty.
    if False not in passing_check_list:
        # Print completion file
        exec_make_completion_file = subprocess.Popen(
            f"touch {job.fn('avg_std_dev_calculated.txt')}",
            shell=True, 
            stderr=subprocess.STDOUT
        )
        os.wait4(exec_make_completion_file.pid, os.WSTOPPED)


# ******************************************************
# ROW'S ENDING CODE SECTION (START)
# ******************************************************
if __name__ == '__main__':
    # Parse the command line arguments: python action.py --action <ACTION> [DIRECTORIES]
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', required=True)
    parser.add_argument('directories', nargs='+')
    args = parser.parse_args()

    # Open the signac jobs
    project = signac.get_project()
    jobs = [project.open_job(id=directory) for directory in args.directories]

    # Call the action
    globals()[args.action](*jobs)
# ******************************************************
# ROW'S ENDING CODE SECTION (END)
# ******************************************************

