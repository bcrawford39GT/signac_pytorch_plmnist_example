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
import numpy as np

# ┌──────────┐
# │ NOTES    │
# └──────────┘

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

# ┌───────────────────────────────────────────────┐
# │ SET THE PROJECTS DEFAULT DIRECTORY AND PATHS  │
# └───────────────────────────────────────────────┘

signac_directory = Path.cwd()

if signac_directory.name != "project":
    raise ValueError(f"Please run this script from inside the `project` directory.")

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

def part_2_download_data_command(*jobs):
    """Download the data."""

    for job in jobs:

        # find the main data directory
        job_search = job.project.find_jobs({"statepoint_type": "main_data"})
        assert len(job_search) == 1
        main_data_job = [*job_search][0]

        # Make the directory
        if not os.path.isdir(main_data_job.fn("MNIST")):

            # Download the data
            exec_download_data = subprocess.Popen(
                f'python -m plmnist.download --data_dir {main_data_job.fn("MNIST")}', 
                shell=True, 
                stderr=subprocess.STDOUT
            )
            os.wait4(exec_download_data.pid, os.WSTOPPED)

        # Check that data has been downloaded and create completion files 
        # in each state point directory.
        if os.path.isdir(main_data_job.fn("MNIST")):
            # Print completion file
            exec_make_completion_file = subprocess.Popen(
                f"touch {job.fn('data_download_complete.txt')}",
                shell=True, 
                stderr=subprocess.STDOUT
            )
            os.wait4(exec_make_completion_file.pid, os.WSTOPPED)


# ┌──────────────────────────────────────────────┐
# │ Part 3 - verify the main data is downloaded  │
# └──────────────────────────────────────────────┘

def part_3_verify_main_data_downloaded_command(*jobs):
    """Verify the main data is downloaded."""

    for job in jobs:

        # find the main data
        job_search = job.project.find_jobs({"statepoint_type": "main_data"})
        assert len(job_search) == 1
        main_data_job = [*job_search][0]

        # Write the completion files in the correct training directories
        if os.path.isfile(main_data_job.fn('data_download_complete.txt')):
            exec_make_completion_file = subprocess.Popen(
                f"touch {job.fn('ready_to_start_training.txt')}",
                shell=True, 
                stderr=subprocess.STDOUT
            )
            os.wait4(exec_make_completion_file.pid, os.WSTOPPED)
                  

# ┌──────────────────────────────────────┐
# │ Part 4 - train and test a neural net │
# └──────────────────────────────────────┘

def part_4_train_and_test_command(*jobs):
    """Run the train + test command."""

    for job in jobs:
        # find the main data
        job_search = job.project.find_jobs({"statepoint_type": "main_data"})
        assert len(job_search) == 1
        main_data_job = [*job_search][0]

        # The below will output the 'results.json' file

        train_command =  (
            f"python -m plmnist "
            f"--num_epochs {int(job.statepoint.num_epochs_int)} "
            f"--log_path {job.path} "
            f"--result_path {job.path} "
            f"--data_dir {main_data_job.fn('MNIST')} "
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
# │ Part 5 - run the FGSM attack │
# └──────────────────────────────┘

def part_5_fgsm_attack_command(*jobs):
    """Run FGSM attack command."""

    for job in jobs:
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

        # Write the completion file if the job finished correcty.
        if False not in passing_check_list:
            # Print completion file
            exec_make_completion_file = subprocess.Popen(
                f"touch {job.fn('fgsm_attack_complete.txt')}",
                shell=True, 
                stderr=subprocess.STDOUT
            )
            os.wait4(exec_make_completion_file.pid, os.WSTOPPED)


# ┌─────────────────────────────────────┐
# │ Part 6 - compute avg/std over seeds │
# └─────────────────────────────────────┘

def part_6_seed_analysis_command(*jobs):
    """Write the output file with the seed averages."""

    if not os.path.isdir(analysis_directory):
        os.system(f"mkdir {analysis_directory}")

    # create document
    test_acc_list = []
    test_loss_list = []
    val_acc_list = []
    val_loss_list = []
    fgsm_acc_list = []

    header = " ".join(
        [
            "num_epochs_int".ljust(25),
            "batch_size_int".ljust(25),
            "hidden_size_int".ljust(25),
            "learning_rate_float".ljust(25),
            "dropout_prob_float".ljust(25),
            "fgsm_epsilon_float".ljust(25),
            "test_acc_avg".ljust(25),
            "test_acc_std_dev".ljust(25),
            "test_loss_avg".ljust(25),
            "test_loss_std_dev".ljust(25),
            "val_acc_avg".ljust(25),
            "val_acc_std_dev".ljust(25),
            "val_loss_avg".ljust(25),
            "val_loss_std_dev".ljust(25),
            "fgsm_acc_avg".ljust(25),
            "fgsm_acc_std_dev".ljust(25),
            "\n",
        ]
    )

    if output_file.exists():
        output_file_obj = open(output_file, "a")
    else:
        output_file_obj = open(output_file, "w")
        output_file_obj.write(header)

    for job in jobs:  # only includes jobs of the same seed
        
        # get the individual values
        with open(job.fn("results.json"), "r") as json_log_file:
            loaded_json_file = json.load(json_log_file)

            test_acc_list.append(loaded_json_file["test_acc"])
            test_loss_list.append(loaded_json_file["test_loss"])
            val_acc_list.append(loaded_json_file["val_acc"])
            val_loss_list.append(loaded_json_file["val_loss"])
            fgsm_acc_list.append(loaded_json_file["fgsm"]["accuracy"])

    output_file_obj.write(
        " ".join( 
            [
                f"{job.statepoint.num_epochs_int: <25}",
                f"{job.statepoint.batch_size_int: <25}",
                f"{job.statepoint.hidden_size_int: <25}",
                f"{job.statepoint.learning_rate_float: <25}",
                f"{job.statepoint.dropout_prob_float: <25}",
                f"{job.statepoint.fgsm_epsilon_float: <25}",
                f"{np.mean(test_acc_list): <25}",
                f"{np.std(test_acc_list, ddof=1): <25}",
                f"{np.mean(test_loss_list): <25}",
                f"{np.std(test_loss_list, ddof=1): <25}",
                f"{np.mean(val_acc_list): <25}",
                f"{np.std(val_acc_list, ddof=1): <25}",
                f"{np.mean(val_loss_list): <25}",
                f"{np.std(val_loss_list, ddof=1): <25}",
                f"{np.mean(fgsm_acc_list): <25}",
                f"{np.std(fgsm_acc_list, ddof=1): <25}",
                "\n",
            ]
        )
    )

    # Check that the replicate (seed) average file has been written and completed properly.
    passing_check_list = []
    if not output_file.exists():
        passing_check_list.append(False)

    with open(output_file, "r") as f:
        lines = f.readlines()

    num_seeds = set()
    for job in jobs:
        num_seeds.add(int(job.statepoint.seed_int))

    num_agg = len(jobs) / len(num_seeds)

    if len(lines) != num_agg + 1:
        passing_check_list.append(False)

    # Write the completion file if the job finished correcty.
    if False not in passing_check_list:
        # Print completion file
        exec_make_completion_file = subprocess.Popen(
            f"touch {job.fn('avg_std_dev_calculated.txt')}",
            shell=True, 
            stderr=subprocess.STDOUT
        )
        os.wait4(exec_make_completion_file.pid, os.WSTOPPED)

    output_file_obj.close()

# ┌───────────────────────────┐
# │ ROW'S ENDING CODE SECTION │
# └───────────────────────────┘
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


