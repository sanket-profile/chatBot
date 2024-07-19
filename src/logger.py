import os
import logging
from datetime import datetime


LOG_FOLDER_PER_DATE=f"{datetime.now().strftime('%m_%d_%Y')}"
LOG_FOLDER_PATH = os.path.join(os.getcwd(),"LOGS",LOG_FOLDER_PER_DATE)
os.makedirs(LOG_FOLDER_PATH,exist_ok=True)

LOG_FILE_NAME = f"{datetime.now().strftime('%H:%M')}.log"
LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH,LOG_FILE_NAME)



logger = logging.getLogger("COMPONENTS")
logger.setLevel(logging.INFO)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[ %(asctime)s  %(lineno)d %(name)s - %(levelname)s - %(message)s]",
    level=logging.INFO
)
