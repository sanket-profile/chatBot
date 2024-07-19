import os

import pandas as pd

from src.utils import generate_session_id
from src.components.data_transformation import dataTransformation
from src.pipeline.rag_pipeline import ragPipeline
from src.exception import CustomException
from src.logger import logger

from langchain_community.document_loaders import HuggingFaceDatasetLoader

from dataclasses import dataclass

@dataclass
class dataIngestionConfig():
    rawDataPath : str = os.path.join(os.getcwd(),"Artifacts","data","rawData.json")

class dataIngestion():
    def __init__(self):
        self.dataIngestionConfig = dataIngestionConfig()

    def initiate_data_ingestion(self):
        try:
            logger.info("Starting Data Ingestion")

            df = pd.read_json("hf://datasets/mandeepbagga/flipkart-phones-description/data.jsonl", lines=True) 

            logger.info("Data Ingestion Completed")
            logger.info("Saving the Raw Data in Artifacts Folder")

            df.to_json(self.dataIngestionConfig.rawDataPath)

            logger.info("Saved the raw data into Artifacts Folder")
        except Exception as e:
            raise CustomException("Something Wrong in initiate_data_ingestion method of dataIngestion class")

        return(
            df,
            self.dataIngestionConfig.rawDataPath
        )
    

if __name__ == "__main__":
    rag_pipeline = ragPipeline()
    chain = rag_pipeline.initiatePipeline()
    config={"configurable": {"session_id": f"{generate_session_id()}"}}
    for i in range(10):
        print(config['configurable']['session_id'])
        input1 = input("Ask the query")
        print(chain.invoke({"input":f"{input1}"},config= config)['answer'])

