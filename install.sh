#!/bin/bash

SYSTEM=$(uname -s)

if [ $SYSTEM = 'Darwin' ]
  then
    # if the system is darwin we are on a mac
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -O ./miniconda_install.sh
    brew install ghostscript
    brew link --overwrite ghostscript
  else
    # otherwise it is a linux machine
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ./miniconda_install.sh
    # assumue ubuntu
    apt install python3-tk ghostscript
fi

if [ $(ls | grep -c miniconda3) ]
  then
    echo "Miniconda3 present, proceeding without download & install"
else
  # PYTHONPATH may cause problems finding the correct python install. Unset before continuing.
  unset PYTHONPATH

  # install miniconda to the directory miniconda3/ with the folling flags
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
# grep -c returns 1 if found else 0.  1 is interpreted as True and thus update is triggered if our
# env is found
if [ "$(conda-env list) | grep -c $ENV_NAME" ]
  then
    conda env update -f requirements.yml
  else
    conda env create -f requirements.yml
fi

# TODO
# git clone workshop materials
# mkdir logs
# touch logs/log.log
# chmod workshop materials

# need to init shell for conda
# and make sure that conda is available to call the source location of our env
# I can use a runscript for this but I'm not sure if it is worth the additional overhead
# for the students.

# Get datasets
mkdir -p data/licenses_by_year

# MJ business licenses data
wget https://data.colorado.gov/api/views/sqs8-2un5/rows.csv?accessType=DOWNLOAD -O ./data/licensed_mj_biz.csv

# MJ tax revenue by county
wget https://data.colorado.gov/api/views/3sm5-jtur/rows.csv?accessType=DOWNLOAD -O ./data/monthly_tx_revenue.csv

# MJ sales revenue
wget https://data.colorado.gov/api/views/j7a3-jgd3/rows.csv?accessType=DOWNLOAD -O ./data/mj_sales_revenue.csv

# County Population by age and year
wget https://data.colorado.gov/api/views/q5vp-adf3/rows.csv?accessType=DOWNLOAD -O ./data/pop_by_age_and_year.csv

# Personal Income by County
wget https://data.colorado.gov/api/views/2cpa-vbur/rows.csv?accessType=DOWNLOAD -O ./data/personal_income.csv

# Unemployment by geographic area
wget https://data.colorado.gov/api/views/4e3w-qire/rows.csv?accessType=DOWNLOAD -O ./data/unemployment_rates.csv

# Dean Runyon industry report pdf
wget https://industry.colorado.com/sites/default/files/DeanRunyan%20EconomicImpact2017.pdf -O ./data/runyon.pdf

# get yearly licenses
# 2019 to august
wget https://www.colorado.gov/pacific/sites/default/files/190801%20Stores_0.xlsx -O ./data/licenses_by_year/retail_aug_2019.xlsx
wget https://www.colorado.gov/pacific/sites/default/files/190801%20Centers.xlsx -O ./data/licenses_by_year/med_aug_2019.xlsx

# 2018
wget https://www.colorado.gov/pacific/sites/default/files/Stores%2012032018.xlsx -O ./data/licenses_by_year/rec_2018.xlsx
wget https://www.colorado.gov/pacific/sites/default/files/Centers%2012032018.xlsx -O ./data/licenses_by_year/med_2018.xlsx

# 2017
wget https://www.colorado.gov/pacific/sites/default/files/Stores%2011012017_1.xlsx -O ./data/licenses_by_year/rec_2017.xlsx
wget https://www.colorado.gov/pacific/sites/default/files/Centers%2012012017_1.xlsx -O ./data/licenses_by_year/med_2017.xlsx

# 2016
wget https://www.colorado.gov/pacific/sites/default/files/Stores%2012012016.xlsx -O ./data/licenses_by_year/rec_2016.xlsx
wget https://www.colorado.gov/pacific/sites/default/files/Centers%2012012016_1.xlsx -O ./data/licenses_by_year/med_2016.xlsx

# 2015
wget https://www.colorado.gov/pacific/sites/default/files/Stores%2012012015_1.pdf -O ./data/licenses_by_year/rec_2015.pdf
wget https://www.colorado.gov/pacific/sites/default/files/Centers%2012012015_1.pdf -O ./data/licenses_by_year/med_2015.pdf

# 2014
wget https://www.colorado.gov/pacific/sites/default/files/Retail%20Stores%2012012014.pdf -O ./data/licenses_by_year/rec_2014.pdf
wget https://www.colorado.gov/pacific/sites/default/files/Centers%2012012014.pdf -O ./data/licenses_by_year/med_2014.pdf




