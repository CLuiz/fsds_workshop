#!/bin/bash

# save args after the flags into a variable
ARGS="${@:2}"

# TODO
# check if the number of items passeed at the commandline is > 1.  If not
# echo help info

# set pathing to use local miniconda
CONDA_PATH="/miniconda3/bin/"
PATH=$(pwd)$CONDA_PATH:$PATH

# get config vars from config file
source "$(pwd)/config.ini"
# set conda env and activate if it exists
# do I need to check if the env is there?

source activate $CONDAENV
export PYTHONPATH="$PATH:$PYTHONPATH"

run_script () {
  echo 'run script called'
  echo "running Flask server at port: $PORT"
  gunicorn -p pid.txt -w $WORKERS --threads $THREADS -b localhost:$PORT \
      --log-level LOG_LEVEL 2>&1 >> $(pwd)$LOGFILE server:app
  exit 0

}
stop_server () {
  echo 'stop server called'
  # PID=$(pgrep python server.py)
  PID="$(< pid.txt)"
  kill $PID
  echo "killing process at pid: $PID"
  exit 0
}
get_info () {
  echo "Config sourced: $CONFIG"
  echo "PORT: $PORT"
  echo "PID: $(< pid.txt)"
  echo "ENV: $CONDAENV"
  echo "THREADS: $THREADS"
  echo "WORKERS: $WORKERS"
  echo "LOG_LEVEL: $LOG_LEVEL"
  echo "LOGFILE: $LOGFILE"
  exit 0
}

get_shell () {
  echo 'get shell called'
  $ARGS
  exit 0
}

get_ipython () {
  echo 'get ipython called'
  ipython
  exit 0
}

get_help () {
  echo 'args'
  echo '-r run script'
  echo '-s get application status'
  echo '-b execute shell with args for commands'
  echo '-i start ipython repl'
  echo '-h show help'
  exit 0
}

check_install () {
  CONDA_VERSION="{which ipython}"
  echo $CONDA_VERSION

}
# https://www.shellscript.sh/tips/getopts/
while getopts 'crsb:ihx' opt
do
  case $opt in
    c) check_install ;;
    r) run_script ;;
    s) get_info ;;
    b) get_shell ;;
    i) get_ipython ;;
    h) get_help ;;
    x) stop_server ;;
  esac
done
