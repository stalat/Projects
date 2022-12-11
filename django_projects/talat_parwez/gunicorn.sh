#!/bin/bash

source venv/bin/activate
cd /var/lib/jenkins/workspace/django-cicd/django_projects/talat_parwez

python3 manage.py makemigrations
python3 manage.py migrate

echo "Migrations done"

# to activate the virtual environment
cd /var/lib/jenkins/workspace/django-cicd/django_projects/

sudo cp -rf gunicorn.socket /etc/systemd/system/
sudo cp -rf gunicorn.service /etc/systemd/system/

echo "$USER"
echo "$PWD"

sudo systemctl daemon-reload
sudo systemctl start gunicorn
