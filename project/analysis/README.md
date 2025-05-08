## Anaysis directory
--------------------

### Overview
The `analysis` directory is typically where the final project analysis files and data are stored.  This does not include the individual state point data or analysis files, which is typically stored in thier respective directories.  This `analysis` directory should remain here, with all the `project.py` file automatically deleting and regenerating the project analysis files and data files, as needed, ensuring that the previous (old) final project analysis files and data are never reused accidentially when the user adds new state points. 

### Examples

Some examples of what can be stored in the `analysis` directory:

 - The averages and standard deviations for all the seeds (replicates) of the provided state points.  
 - Any other data final data that is calculated from the state points, which is used as the final results.
 - Any manual plotting files that are run on the final data.  Manual plotting scripts are sometimes prefferred here, as the data many need manipulated, scaled, etc., in ways are hard to include in any automated and general `project.py` script.  
