git pull
python3.9 api.py |& tee -a ./log/"$(date +"%Y/%m/%d_%H_%M_%S_%3N").log"

