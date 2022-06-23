git pull
python3 api.py |& tee -a "$(date +"%Y_%m_%d_%I_%M_%p").log"
