#!/bin/bash
cd /home/ubuntu/fmp-usage-forecaster
source venv/bin/activate
git pull
python -m pip install -r requirements.txt
python pred_app.py > /dev/null 2>&1
