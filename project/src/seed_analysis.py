import json, typing

import numpy as np


if typing.TYPE_CHECKING:
    from signac.job import Job


# helper function for aggregating on all config keys except for seed
'''
def statepoint_without_seed(job: "Job"):
    """Return the statepoint dictionary without the seed."""
    return [(k, v) for k, v in job.statepoint.items() if k != "seed_int"]
'''

def seed_analysis(aggregated_jobs, output_file):
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

    for job in aggregated_jobs:  # only includes jobs of the same seed
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

    output_file_obj.close()
