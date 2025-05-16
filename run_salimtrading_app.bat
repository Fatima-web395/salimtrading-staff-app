@echo off
echo Setting up your SalimTrading Staff App...
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo Starting the Flask server...
python app.py
pause
