## Signac Workflow Tutorial: MNIST Example using PyTorch Lightning
------------------------------------------------------------------

## General Notes

Using `signac` and `row` workflows provide the following benefits: 

 - The `signac` and `row` workflows provide contained and totally reproducible results, since all the project steps and calculations are contained within this a single `signac`/`row` project. Although, to ensure total reproduciblity, the project should be run from a container.  Note: This involves building a container (Docker, Apptainer, Podman, etc.), using it to run the original calculations, and providing it the future parties that are trying to reproduce the exact results.

 - The `signac` and `row` workflows can simply track the progress of any project locally or on the HPC, providing as much or a little details of the project status as the user programs into the `actions.py` and `workflow.toml` file.  Note: `row` tracks the progress and completion of a project step or section by determining if a file exists.  Therefore, the user can generate this file after a verification step is performed to confirm a sucessful completion or commands run without error (Exampe: `Exit Code 0`).  

 - These `signac` and `row` workflows are designed to track the progress of all the project's parts or stages, only resubmitting the jobs locally or to the HPC if they are not completed or not already in the queue.
 
 - These `signac` and `row` workflows also allow colleagues to quickly transfer their workflows to each other, and easily add new state points to a project, without the fear of rerunning the original state points.  

 - Please also see the [signac website](https://signac.io/) and [row website](https://row.readthedocs.io/), which outlines some of the other major features. 

 - **src directory:** This directory can be used to store any other custom function that are required for this workflow.  This includes any developed `Python` functions or any template files used for the custom workflow (Example: A base template file that is used for a find and replace function, changing the variables with the differing state point inputs).  


## Overview

This is a `signac` Workflow example/tutorial for a pytorch using plmnist, which utilizes the following workflow steps:

- **Part 1:** For each individual job (set of state points), this code generates the `signac_job_document.json` file from the `signac_statepoint.json` data.  The `signac_statepoint.json` only stores the set of state points or required variables for the given job.  The `signac_job_document.json` can be used to store any other variables that the user wants to store here for later use or searching. 

- **Part 2:** This downloads the dataset used for the pytorch and plmnist calculations, which will be used to do a calculation/model in `Part 3`.  

- **Part 3:** Checks to see if `Part 4` can be run, and if so, prints a file to signify that. 

- **Part 4:** Run pytorch for the plmnist model without fgsm, using bash command to run a software package inside the commands for each state point. 

- **Part 5:** Run the fgsm on the model from `Part 4`, using bash command to run a software package inside the commands for each state point.  

- **Part 6:** Obtain the average and standard deviation for each input value combination (`num_epochs`, `batch_size`, `hidden_size`, `learning_rate`, `dropout_prob`, `fgsm_epsilon`), with different `seed` values (replicates). The user can add more values at any time via the `init.py` file and rerun only the added value calculations.  The averages and standard deviations accoss the different `seed` values (replicates) are determined for the `test_acc_avg`, `test_acc_std`, `test_loss_avg`, `test_loss_std`, `val_acc_avg`, `val_acc_std`, `val_loss_avg`, `val_loss_std`, `fgsm_acc_avg`, and `fgsm_acc_std` values, and added to the `analysis/output_avg_std_of_seed_txt_filename.txt` file.


## Resources
 - The [signac documentation](https://signac.io/) and the [signac GitHub](https://github.com/glotzerlab/signac) can be used for reference.

## Citation

Please cite this GitHub repository and the repository in which the work was based off of.

 - This repository. https://github.com/pace-gt/signac_pytorch_plmnist_example/blob/main/project/project.py
 - PyTorch Lightning. lightning.ai/docs/pytorch/stable/notebooks/lightning_examples, accessed November 2023.

## Authors

- Brad Crawford and Michael Klamkin. Signac Workflow Tutorial: MNIST Example using PyTorch Lightning. GitHub, 2023 

## Installation

These signac workflows "this project" can be built using conda:

### Install the main signac packages:
```bash
cd signac_pytorch_plmnist_example
```

##### For CPU only installations:

> [!WARNING]  !! **Warning** !!
> 
> If you use the CPU build  (`cpu_environment.yml`) you will have to also modify 
> Part 4 in the `workflow.toml`, removing the GPU requirement and selecting the 
> correct partiions, etc. 
> Not doing this will result in errors in submitting and running Part 4.

```bash
mamba env create --file cpu_environment.yml
```

##### For GPU installations:
```bash
mamba env create --file gpu_environment.yml
```

### Activate the conda environment:
```bash
mamba activate plmnist
```

### Install the plmnist package:

```bash
pip install -e .
```

## HPC setup
------------
- All the signac and row commands are run from the `<local_path>/signac_numpy_tutorial/signac_numpy_tutorial/project directory`.

The `clusters.toml` file is used to specify the the HPC environment.  The specific HPC will need to be setup for each HPC and identified on the `workflow.toml` file.    

The following files are located here:

```bash
cd <you_local_path>/signac_pytorch_plmnist_example/signac_pytorch_plmnist_example/project
```

### **Modify and add the `clusters.toml` file:**


- Modify the `clusters.toml` file to fit your HPC.
  1. Replace the **`<ADD_YOUR_HPC_NAME_STRING>`** values with your unique HPC name as a string.
     
     For Example at GT, `<ADD_YOUR_HPC_NAME_STRING>` is replaced with `"phoenix"`.
     
  2. You also may need to change the `"LMOD_SYSHOST"` environment variable to match how your specific HPC is setup. 

- **Add the modified cluster configuration file (`clusters.toml`) to the following location on the HPC under your account (`~/.config/row/clusters.toml`).**

```bash
cp clusters.toml ~/.config/row/clusters.toml
```

### **Modify and add the `workflow.toml` file:**
- Modify the `workflow.toml` file to fit your HPC.
  1. Replace the **`<ADD_YOUR_HPC_NAME>`** values with your unique HPC name.
     
     For Example at GT, `<ADD_YOUR_HPC_NAME>` is replaced with `phoenix`, changing `[action.submit_options.<ADD_YOUR_HPC_NAME>]` to `[action.submit_options.phoenix]`.
     
  2. **`<ADD_YOUR_CHARGE_ACCOUNT_NAME_STRING>`** values with your specific charge account as a string.
    
     For Example, `<ADD_YOUR_CHARGE_ACCOUNT_NAME_STRING>` is replaced with `"project_x"`, changing `account = `<ADD_YOUR_CHARGE_ACCOUNT_NAME_STRING>``  `account = "project_x"`
     
- Modify the slurm submission script, or modify the `workflow.toml` file to your cluster's partitions that you want to use, you can do that with the below addition to the `workflow.toml` file.

For parts 1, 2, 3, 4, and 5, add the CPU partion(s) you want to use:

    ```bash
    custom = ["","--partition=cpu-1,cpu-1,cpu-3"]
    ```

For part 4, add the GPU partion(s) you want to use:

    ```bash
    custom = ["","--partition=gpu-1,gpu-1,gpu-3"]
    ```

Note: The cluster partitions in the `clusters.toml` can be specified for each HPC or only the partitions that you commonly use.  This allows you to specify the partition in the `workflow.toml` file (i.e., `partition=real_partition_name`), and does not need the partitions to be specified/overwritten in the `custom` line (i.e, `custom = ["","--partition=cpu-1,cpu-1,cpu-3"]`.

Note: As needed, the cluster partitions in the `clusters.toml` can be fake ones.  Then specifying a fake partition in the `workflow.toml` file (i.e., `partition=fake_partition_name`), allows you just override the selected partition and allow many real partitions in the `workflow.toml` (i.e., `custom = ["","--partition=cpu-1,cpu-1,cpu-3"]`), which is used to write the `Slurm` submission script.
- This can also be done if >1 or more partitions is needed.

### Testing the setup for running **on an HPC**.

**Build the test workspace:**     

```bash
python init.py
```

**Run the following command as the test:**   

```bash
row submit --dry-run
```
    
**You should see an output that looks something like this (<u>export ACTION_CLUSTER=`<YOUR_HPC_NAME>`</u>) in the output if it is working:**

```bash
...

directories=(
be31aae200171ac52a9e48260b7ba5b1
)

export ACTION_WORKSPACE_PATH=workspace
export ACTION_CLUSTER=<YOUR_HPC_NAME>

...
```

**Clean up row and delete the test workspace:**    

```bash
row clean
```

```bash
rm -r workspace
```

### Testing the setup for running **on an HPC**.
-----------------------------------------------

**Build the test workspace:**     

```bash
python init.py
```

**Run the following command as the test:**   

```bash
row submit --dry-run
```
    
**You should see an output that looks something like this (<u>export ACTION_CLUSTER=`<YOUR_HPC_NAME>`</u>) in the output if it is working:**

```bash
...

directories=(
be31aae200171ac52a9e48260b7ba5b1
)

export ACTION_WORKSPACE_PATH=workspace
export ACTION_CLUSTER=<YOUR_HPC_NAME>

...
```

**Clean up row and delete the test workspace:**    

```bash
row clean
```

```bash
rm -r workspace
```

## Local Setup
--------------

- If `row submit` is run locally like this, then you must remove the HPC parts in the `workflow.toml` file (see the notes in the `workflow.toml`).
- Change the GPU parts to run only on CPU, if the local hardware is supports CPU workflows (see the notes in the `workflow.toml`).

### Testing the setup for running only locally, **not on an HPC**. 
------------------------------------------------------------------ 

**Build the test workspace:**     

```bash
python init.py
```

**Run the following command as the test:**       

```bash
row submit --dry-run
```

**You should see an output that looks something like this (<u>export ACTION_CLUSTER=\`none\`</u>) in the output if it is working:**

```bash
...

directories=(
be31aae200171ac52a9e48260b7ba5b1
)

export ACTION_WORKSPACE_PATH=workspace
export ACTION_CLUSTER=`none`

...
```

**Clean up row and delete the test workspace:**    

```bash
row clean
```

```bash
rm -r workspace
```
