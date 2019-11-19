#!/bin/bash

CONDA_PATH="/miniconda3/bin/"
PATH=$(pwd)$CONDA_PATH:$PATH
source activate ourenv
ipython
