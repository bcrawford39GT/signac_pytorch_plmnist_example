"""Signac implementation for the plmnist project."""

import json, datetime
from pathlib import Path

import hpc_setup
from flow import FlowProject, aggregator
from signac import get_project
from signac.job import Job

from src.seed_analysis import seed_analysis, statepoint_without_seed

# Set the walltime, memory, and number of CPUs and GPUs needed
# for each individual job, based on the part/section.
# *******************************************************
# *******************   Notes   ************************* 
# The "np" or "ntasks" (i.e., number or tasks) in the 
# "@FlowProject.operation(directives= dict( 
# walltime=0.5, 
# mem-per-cpu=4, 
# np=1, 
# cpus-per-task=1,
# gpus-per-task=0
# )" 
# should be 1 for most cases.
# *******************************************************
# *******************   WARNING   ***********************
# It is recommended to check all HPC submisstions with the
# '--pretend' command so you do not make an errors requesting 
# the CPUs, GPUs, and other parameters by its value 
# that many cause more resources to be used than expected,
# which may result in higher HPC or cloud computing costs! 
# *******************   WARNING   ***********************
# *******************************************************
# *******************   Notes   ************************* 
# *******************************************************
# *******************************************************

# setup paths
signac_directory = Path.cwd()

if signac_directory.name != "project":
    raise ValueError(f"Please run this script from inside the `project` directory.")

data_directory = signac_directory.parent / "data"
output_file = signac_directory / "analysis" / "output.txt"


# ┌─────────────────────────────────┐
# │ Part 1 - write the job document │
# └─────────────────────────────────┘


# post-condition: the job document has been written
@FlowProject.label
def part_1_initialize_signac_completed(job: Job):
    """Check that the job document has been written."""
    return job.isfile("signac_job_document.json")


# operation: write the job document
@FlowProject.post(part_1_initialize_signac_completed)
@FlowProject.operation(
    directives=
    {
        "np": 1,
        "cpus-per-task": 1,
        "gpus-per-task": 0,
        "mem-per-cpu": 4,
        "walltime": 0.1,
    },
    with_job=True,
)
def part_1_initialize_signac_command(job: Job):
    """Set the system's job parameters in the json file."""
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


# post-condition: the data has been downloaded
@FlowProject.label
def part_2_download_data_completed(*jobs: Job):
    """Check that data has been downloaded."""
    return data_directory.exists() and (data_directory / "MNIST").exists()


# operation: download the data
@FlowProject.pre(lambda *jobs: all(part_1_initialize_signac_completed(j) for j in jobs))
@FlowProject.post(part_2_download_data_completed)
@FlowProject.operation(
    directives=
    {
        "np": 1,
        "cpus-per-task": 1,
        "gpus-per-task": 0,
        "mem-per-cpu": 4,
        "walltime": 0.2,
    },
    cmd=True,
    aggregator=aggregator(),
)
def part_2_download_data_command(*jobs: Job):
    """Download the data."""
    data_directory.mkdir(parents=True, exist_ok=True)

    # Download the data set via a bash command
    return f"python -m plmnist.download --data_dir {data_directory}"


# ┌──────────────────────────────────────┐
# │ Part 3 - train and test a neural net │
# └──────────────────────────────────────┘


# post-condition: the results file exists
@FlowProject.label
def part_3_train_and_test_completed(job: Job):
    """Check if the results file exists."""
    return job.isfile("results.json")


# operation: run the train + test command
@FlowProject.pre(part_1_initialize_signac_completed)
@FlowProject.pre(part_2_download_data_completed)
@FlowProject.post(part_3_train_and_test_completed)
@FlowProject.operation(
    directives=
    {
        "np": 1,
        "cpus-per-task": 1,
        "gpus-per-task": 1,
        "mem-per-cpu": 4,
        "walltime": 1.0,
    },
    with_job=True,
    cmd=True,
)
def part_3_train_and_test_command(job: Job):
    """Run the train + test command."""
    output_file.unlink(missing_ok=True)

    print(f"Running training/testing for {job}")
    return (
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


# ┌──────────────────────────────┐
# │ Part 4 - run the FGSM attack │
# └──────────────────────────────┘


# post-condition: the results contains the fgsm keys
@FlowProject.label
def part_4_fgsm_attack_completed(job: Job):
    """Check if the training, testing, and writing are completed properly."""
    if not job.isfile("results.json"):
        return False
    else:
        with open(job.fn("results.json"), "r") as json_log_file:
            try:
                loaded_json_file = json.load(json_log_file)
            except json.decoder.JSONDecodeError:
                return False

            for key in ["fgsm", "test_loss", "test_acc"]:
                if key not in loaded_json_file:
                    return False
                elif key == "fgsm":
                    if "accuracy" not in loaded_json_file["fgsm"]:
                        return False

            return True


# operation: run the fgsm attack command
@FlowProject.pre(part_3_train_and_test_completed)
@FlowProject.post(part_4_fgsm_attack_completed)
@FlowProject.operation(
    directives=
    {
        "np": 1,
        "cpus-per-task": 1,
        "gpus-per-task": 0,
        "mem-per-cpu": 4,
        "walltime": 0.5,
    },
    with_job=True,
    cmd=True,
)
def part_4_fgsm_attack_command(job: Job):
    """Run FGSM attack command."""
    output_file.unlink(missing_ok=True)

    print(f"Running fgsm for {job}")
    return (
        f"python -m plmnist.fgsm "
        f"--seed {int(job.statepoint.seed_int)} "
        f"--result_path {job.path} "
        f"--fgsm_epsilon {float(job.statepoint.fgsm_epsilon_float)} "
    )


# ┌─────────────────────────────────────┐
# │ Part 5 - compute avg/std over seeds │
# └─────────────────────────────────────┘


# post-condition: the replicate (seed) average file has been written
@FlowProject.label
def part_5_seed_analysis_completed(*jobs: Job):
    """Check that the replicate (seed) average file has been written."""
    if not output_file.exists():
        return False

    with open(output_file, "r") as f:
        lines = f.readlines()

    project = get_project()

    num_seeds = set()
    for job in project:
        num_seeds.add(job.statepoint.seed_int)

    num_agg = len(project) / len(num_seeds)

    if len(lines) != num_agg + 1:
        return False

    return True


# operation: write the output file with the seed averages
@FlowProject.pre(lambda *jobs: all(part_4_fgsm_attack_completed(j) for j in jobs))
@FlowProject.post(part_5_seed_analysis_completed)
@FlowProject.operation(
    directives=
    {
        "np": 1,
        "cpus-per-task": 1,
        "gpus-per-task": 0,
        "mem-per-cpu": 4,
        "walltime": 0.6,
    },
    aggregator=aggregator.groupby(
        key=statepoint_without_seed, sort_by="seed_int", sort_ascending=False
    ),
)
def part_5_seed_analysis_command(*aggregated_jobs: Job):
    """Write the output file with the seed averages."""
    seed_analysis(aggregated_jobs, output_file)


if __name__ == "__main__":
    try:
        pr = FlowProject()
    except LookupError as e:
        raise LookupError("Could not find project. Did you run init.py?") from e

    pr.main()
