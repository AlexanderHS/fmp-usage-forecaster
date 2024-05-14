#!/bin/bash
# only need this if venv folder missing
sudo apt-get update
sudo apt-get install python3 python3-venv python3-dev python3-pip authbind freetds-dev freetds-bin unixodbc-dev tdsodbc build-essential libssl-dev libffi-dev unixodbc unixodbc-dev freetds-dev tdsodbc freetds-bin -y
pip3 install pyodbc
python3 -m venv venv
source venv/bin/activate
#sudo touch /etc/authbind/byport/80
#sudo chmod 777 /etc/authbind/byport/80
pip install wheel
pip install flask pyODBC flask_wtf waitress requests wtforms_components python-dateutil
sudo cp freetds.conf /etc/freetds/freetds.conf
sudo cp odbcinst.ini /etc/odbcinst.ini
sudo cp odbc.ini /etc/odbc.ini

# Service Setup
sudo cp fmp-usage-forecaster.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fmp-usage-forecaster.service
sudo systemctl start fmp-usage-forecaster.service
