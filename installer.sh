#!/bin/bash

echo "Installing Occopus..."

if [ -d "$HOME/occopus" ] || [ -d "$HOME/.occopus" ]; then
  echo "Directories $HOME/occopus or $HOME/.occopus already exist! Rename or remove them and rerun this installer!"
  echo "Exiting..."
  exit 1
fi

sudo apt-get -y -qq install python python-pip python-dev python-virtualenv 
sudo apt-get -y -qq install libffi-dev libssl-dev
sudo apt-get -y -qq install redis-server mysql-client

virtualenv $HOME/occopus; 
source $HOME/occopus/bin/activate; 
pip install --upgrade pip; 
pip install --find-links http://pip.lpds.sztaki.hu/packages \
	    --no-index --trusted-host pip.lpds.sztaki.hu OCCO-API;
mkdir -p $HOME/.occopus;
curl -s https://raw.githubusercontent.com/occopus/docs/devel/tutorial/.occopus/occopus_config.yaml \
     -o $HOME/.occopus/occopus_config.yaml; 
curl -s https://raw.githubusercontent.com/occopus/docs/devel/tutorial/.occopus/auth_data.yaml \
     -o $HOME/.occopus/auth_data.yaml;
echo;
echo "Configuration file and authentication template have been copied to"\
     "\"$HOME/.occopus\" directory.";
echo "Fill authentication template with credentials before using Occopus!";
echo "Do not forget to activate your virtualenv before using Occopus!";
echo "Run \"source $HOME/occopus/bin/activate\"";

