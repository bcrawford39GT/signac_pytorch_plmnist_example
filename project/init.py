"""Initialize signac statepoints."""
from pathlib import Path

import os
import signac
import shutil
import subprocess


signac_directory = Path.cwd()

if signac_directory.name != "project":
    raise ValueError(f"Please run this script from inside the `project` directory.")

project = signac.init_project()


# ┌───────────────────────────┐
# │ Define statepoints to run │
# └───────────────────────────┘


num_epochs_int_list = [1, 5]
batch_size_int_list = [128]
hidden_size_int_list = [64]
learning_rate_float_list = [2e-4]
dropout_prob_float_list = [ 0.1, 0.5] #[0.0, 0.1, 0.5]
fgsm_epsilon_float_list = [0.05]
seed_int_list = [1, 2] #[1, 2, 3]


# ┌────────────────────────────────────────┐
# │ Create list of statepoint dictionaries │
# └────────────────────────────────────────┘


all_statepoints = []
for num_epochs_int_i in num_epochs_int_list:
    for batch_size_int_i in batch_size_int_list:
        for hidden_size_int_i in hidden_size_int_list:
            for learning_rate_float_i in learning_rate_float_list:
                for dropout_prob_float_i in dropout_prob_float_list:
                    for fgsm_epsilon_float_i in fgsm_epsilon_float_list:
                        for seed_int_i in seed_int_list:
                            statepoint = {
                                "num_epochs_int": num_epochs_int_i,
                                "batch_size_int": batch_size_int_i,
                                "hidden_size_int": hidden_size_int_i,
                                "learning_rate_float": learning_rate_float_i,
                                "dropout_prob_float": dropout_prob_float_i,
                                "fgsm_epsilon_float": fgsm_epsilon_float_i,
                                "seed_int": seed_int_i,
                            }

                            all_statepoints.append(statepoint)


# ┌────────────────────────┐
# │ Initialize statepoints │
# └────────────────────────┘

for sp in all_statepoints:
    project.open_job(statepoint=sp).init()

# ┌────────────────────────────────────┐
# │ Delete prior analaysis             │
# └────────────────────────────────────┘

# Delete any analysis files that require analysis
# outside a single workspace file and reset row, 
# as row does not dynamically recheck for completion 
# status after the task is completed.  
# If any previous replicate averages and std_devs exist delete them, 
 # because they will need recalculated as more state points were added.

main_analysis_dir_path_and_name = "analysis"
try:
    if os.path.isdir(f'{main_analysis_dir_path_and_name}'):
        shutil.rmtree(f'{main_analysis_dir_path_and_name}')
except:
    print(
        f"No directory named "
        f"'{main_analysis_dir_path_and_name}' exists."
        )

# The 'avg_std_dev_calculated.txt' file are auto-deleted when 
# the 'init.py' file is run.  So if there are errors with this, 
# you can run 'python init.py' and it will reset it, so you can 
# rerun it. 
# This also resets and recalculated the completion status.
try:
    # Delete the 'avg_std_dev_calculated.txt' file
    exec_delete_avg_std_dev_file = subprocess.Popen(
        "rm workspace/*/avg_std_dev_calculated.txt", 
        shell=True, 
        stderr=subprocess.STDOUT
    )
    os.wait4(exec_delete_avg_std_dev_file.pid, os.WSTOPPED)

    # Clean and reset row's completion status
    exec_reset_row_status = subprocess.Popen(
        "row clean --completed && row scan", 
        shell=True, 
        stderr=subprocess.STDOUT
    )
    os.wait4(exec_reset_row_status.pid, os.WSTOPPED)

except:
    print(f"ERROR: Unable to delete the 'avg_std_dev_calculated.txt' file or clean and scan workspace progress.") 