---
title: Rosetta Stone of Job Managers
date: 2015-07-24T17:55:00-07:00
last_mod: "July 24, 2015"
parentDirs: [ hpc-howtos ]
---


<table class="table table-striped table-bordered" style="text-align:center; font-size:14px;">
    <thead>
        <tr>
            <th></th>
            <th>SGE</th>
            <th>Torque</th>
            <th>PBSpro</th>
            <th>LSF</th>
            <th>SLURM</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Submit a job</td>
            <td colspan="3">qsub submit.sh</td>
            <td>bsub &lt; submit.sh</td>
            <td>sbatch submit.sh</td>
        </tr>
        <tr>
            <td>Watch a job</td>
            <td colspan="3">qstat -j 12345</td>
            <td>bjobs 12345</td>
            <td>squeue -j 12345</td>
        </tr>
        <tr>
            <td>Delete a job</td>
            <td colspan="3">qdel 12345</td>
            <td>bkill 12345</td>
            <td>scancel 12345</td>
        </tr>
        <tr>
            <td>Job script option prefix</td>
            <td>#$</td>
            <td colspan="2">#PBS</td>
            <td>#BSUB</td>
            <td>#SBATCH</td>
        </tr>
        <tr>
            <td>Wallclock limit</td>
            <td>-l h_rt=1:300:00</td>
            <td colspan="2">-l walltime=1:30:00</td>
            <td>-W 1:30</td>
            <td>-t 1:30:00</td>
        </tr>
        <tr>
            <td>Total core count (e.g., 64-core MPI job)</td>
            <td>-pe XYZ 64</td>
            <td>-l nodes=4:ppn=16</td>
            <td>-l select=4:ncpus=16</td>
            <td colspan="2">-n 64</td>
        </tr>
        <tr>
            <td>Cores per node (e.g., 4-thread OpenMP job)</td>
            <td>complicated</td>
            <td>-l nodes=1:ppn=4</td>
            <td>-l select=1:ncpus=4</td>
            <td>-R span&#91;ptile=4&#93;"</td>
            <td>-N 1 -n 4</td>
        </tr>
        <tr>
            <td>Nodes+cores (e.g., MPI+OpenMP on 16-core nodes)</td>
            <td>complicated</td>
            <td>complicated</td>
            <td>-l select=4:ncpus=16:mpiprocs=4</td>
            <td>-R span&#91;ptile=16&#93;" -n 64</td>
            <td>-N 4 -n 64</td>
        </tr>
        <tr>
            <td>Mem per process</td>
            <td>-l mem_free=2G</td>
            <td colspan="2">-l pmem=2gb</td>
            <td>n/a</td>
            <td>--mem-per-cpu=2048</td>
        </tr>
        <tr>
            <td>Mem per node</td>
            <td>n/a</td>
            <td colspan="2">-l mem=32gb</td>
            <td>-R "rusage&#91;mem=32768&#93;"</td>
            <td>--mem=32768</td>
        </tr>
        <tr>
            <td>Queue name</td>
            <td colspan="4">-q myqueue</td>
            <td>-p myqueue</td>
        </tr>
        <tr>
            <td rowspan="2">Account number</td>
            <td rowspan="2" colspan="2">-A myacct</td>
            <td>-A myacct</td>
            <td rowspan="2">-P myacct</td>
            <td rowspan="2">-A myacct</td>
        </tr>
        <tr><td>-W group_list=myacct</td></tr>
        <tr>
            <td>Stdout file name</td>
            <td colspan="5">-o stdout.txt</td>
        </tr>
        <tr>
            <td>Stderr file name</td>
            <td colspan="5">-e stderr.txt</td>
        </tr>
        <tr>
            <td>Job name</td>
            <td colspan="3">-N myjob</td>
            <td colspan="2">-J myjob</td>
        </tr>
        <tr>
            <td>Execution shell</td>
            <td colspan="3">-S /bin/bash</td>
            <td>-L /bin/bash</td>
            <td>n/a</td>
        </tr>
    </tbody>
</table>
