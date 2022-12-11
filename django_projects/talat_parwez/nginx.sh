#!bin/bash

sudo cp -rf talat_parwez.conf /etc/nginx/conf.d
chmod 710 /var/lib/jenkins/workspace/django-cicd/django_projects/talat_parwez

sudo nginx -t 

sudo systemctl start nginx
sudo systemctl enable nginx

echo "Nginx has been started"
sudo systemctl status nginx