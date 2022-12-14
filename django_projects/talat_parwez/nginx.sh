#!/bin/bash

cd /var/lib/jenkins/workspace/django-cicd/django_projects/talat_parwez
sudo cp -rf talat_parwez.conf /etc/nginx/sites-available/talat_parwez
chmod 710 /var/lib/jenkins/workspace/django-cicd/django_projects/talat_parwez

sudo ln -s /etc/nginx/sites-available/talat_parwez /etc/nginx/sites-enabled
sudo nginx -t 

sudo systemctl start nginx
sudo systemctl enable nginx

echo "Nginx has been started"
sudo systemctl status nginx