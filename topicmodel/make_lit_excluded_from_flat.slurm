#!/bin/bash
###############################################################################
##                                                                           ##
##                           Campus Cluster                                  ##
##                    Sample OpenMP Job Batch Script                         ##
##                                                                           ##
## SLURM Options (To view, run the following command below)                  ##
##                                                                           ##
##     man sbatch                                                            ##
##                                                                           ##
###############################################################################
#                                                                            
#SBATCH --time=04:00:00                    # Job run time (hh:mm:ss)
#SBATCH --nodes=1                          # Number of nodes
#SBATCH --ntasks-per-node=18               # Number of task (cores/ppn) per node
#SBATCH --job-name=makeexcldata             # Name of batch job
#SBATCH --partition=IllinoisComputes              # Partition (queue)
#SBATCH --account=tunder-ic           
#SBATCH --output=makeexcldata.o%j                # Name of batch job output file
##SBATCH --error=makeexcldata.e%j                # Name of batch job error file
##SBATCH --mail-user=tunder@illinois.edu  # Send email notifications
##SBATCH --mail-type=BEGIN,END             # Type of email notifications to send
#                                                                            
###############################################################################

# Change to the directory from which the batch job was submitted
# Note: SLURM defaults to running jobs in the directory where
# they are submitted, no need for cd'ing to $SLURM_SUBMIT_DIR

#cd ${SLURM_SUBMIT_DIR}

# Add scripts to run here
bin/mallet import-file --input ../novelty/topicmodel/ExcludedFromFlat.txt --use-pipe-from ../novelty/topicmodel/LitstudiesFlat.mallet --output ../novelty/topicmodel/ExcludedFromFlat.mallet --keep-sequence --token-regex '\p{L}[\p{L}\p{P}]*\p{L}|\p{L}'
