#!/bin/bash
cd /home/ubuntu/fmp-usage-forecaster
source venv/bin/activate
git pull
python -m pip install -r requirements.txt
python main.py
