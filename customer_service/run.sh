#!/bin/bash

# Set environment variables to suppress TensorFlow warnings
export TF_CPP_MIN_LOG_LEVEL=2
export GLOG_minloglevel=2

# Run the main application
python main.py "$@" 