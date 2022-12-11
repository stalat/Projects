#!/bin/bash

# For virtual environment
if [-d "env"]
then
  echo "Python virtual env exists"
else
  python3 -m venv venv
fi

echo $PWD
source venv/bin/activate

pip install -r django_projects/talat_parwez/requirements.txt

# For log files
if [-d "logs"]
then
  echo "Log folder exists"
else
  mkdir logs
  touch logs/error.log logs/access.log
fi

sudo chmod -R 777 logs
echo "Environment setup is finished"