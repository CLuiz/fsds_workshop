#!/bin/bash

SYSTEM=$(uname -s)

if [ $SYSTEM = 'Darwin' ]
  then
    # if the system is darwin we are on a mac
    curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -o ./miniconda_install.sh
    brew install ghostscript
    brew link --overwrite ghostscript
  else
    # otherwise it is a linux machine
    curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o ./miniconda_install.sh
    # assumue ubuntu
    sudo apt-get update
    sudo apt-get install python3-tk ghostscript
fi

if [ -d $(pwd)/miniconda3 ]
  then
    echo "Miniconda3 present, proceeding without download & install"
else
  # PYTHONPATH may cause problems finding the correct python install. Unset before continuing.
  unset PYTHONPATH

  # install miniconda to the directory miniconda3/ with the following flags
  # -b: silent mode. Also prevents writing to bashprofile.
  # -u: updates in the case miniconda is already installed
  # -p: sets installation path
  bash ./miniconda_install.sh -b -u -p ./miniconda3/

  # remove installer in the background
  rm miniconda_install.sh &
fi

# set location of miniconda binaries
CONDA_PATH="/miniconda3/bin/"

# export update path so the system can find conda
export PATH=$(pwd)$CONDA_PATH:$PATH

# update conda base environment with the following flags:
# -n: set environment name to update (base is the standard conda env)
# -y: have the system respond 'y' to the user input prompt yes/no to install
# -c: set the channel rom which to update from.
conda update -n base -y -c conda-forge conda

# create conda environment from specifications in the environment.yml file
# get env name from yaml
ENV_NAME=$(grep name requirements.yml | sed 's/.*: //')

# if env exists update,  else create
# grep -c returns 1 if found else 0. 0 is interpreted as True and thus update is triggered if our
# env is found.
if [ "$(conda-env list | grep -c $ENV_NAME || true)" ];
  then
    echo 'Local conda env detected - updating packages'
    conda env update -f requirements.yml
else
    echo 'Local conda env not detected - creating env'
    conda env create -f requirements.yml
fi

# Create log directory
mkdir -p logs
# Get logfile name from the config file
LOGFILE=$(grep LOGFILE config.ini | cut -d "=" -f2)
# Create logfile
touch $LOGFILE

chmod 755 get_data.sh
# get data
./get_data.sh

# chmod workshop materials
chmod -R 755 .
