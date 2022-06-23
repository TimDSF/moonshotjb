clear
git pull
python3.9 api.py |& tee -a ./log/"$(date +"%Y_%m_%d_%H_%M_%S_%3N").log"

