# VeRoLog-2019-MILP
Solution for the VeRoLog Solver Challenge 2019 in a Mixed-integer linear program

Jupyter notebooks were used to develop most of the code, more explanation on the code can be found there. The python files (.py) are used to automate the execution of the MILP including reading the input file and writing a solution file.

First the MILP was implemented by using the Python Pulp package, this did not provide a feasible solution, I was unable to find out why. The code is in the 'Build_MILP_VeRoLog_Pulp' Notebook.

After the failed attempt with Pulp I used the Python MIP package. The Build_MILP_VeRoLog_mip files have multiple versions, because it was better to continue in a complete different file if a fundamental decision was made on the model. Version 03 has the final model and there is clearly explained how all the cost functions and constraints are added to the model. So the reader is advised to start with v03.

In Build_MILP_VeRoLog_mip_v01, here the decision variables y_{thij} and x_{tkij} had edges (i,j) that connected the entire graph, so for example there was a variable where a truck could move to a technician home or where a technician can move to another technician's home
In Build_MILP_VeRoLog_mip_v02, the decision variable x_{tkij} was no longer connected to the technician homes, because the trucks do not have to travel there.
In Build_MILP_VeRoLog_mip_v03, it was decided that instead of having a skillset constraint the y_{thij} variable will only contain edge (i,j) if technician h can install at j or if it is it's home location.

In the "Read_VeRoLog_Instances" Notebook, the code was developed to automatically transform input files into data that is usable to create the MILP.

In the 'RunMILPVeRoLogMip' python file the MILP algorithm can be executed for multiple instances, all functions developed in the 'Build_MILP_VeRoLog_mip_v03' Notebook are used there. This file is dependent on two other files:
 - The 'ReadVeRoLogInstances' python file is used to read the input file and transform it into usuable data for the MILP
 - The 'WriteSolutionVeRoLogMip' python file transforms the MILP outcome into an output file that can be validated by the 'SolutionVerolog2019' python file

The 'SolutionVerolog2019','baseParser' and 'InstanceVerolog2019' pythong files are used to validate if the solution file has a valid solution.
