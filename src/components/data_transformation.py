import os

import numpy as np
import pandas as pd

from langchain_community.document_loaders import DataFrameLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from src.exception import CustomException
from src.logger import logger

from dataclasses import dataclass
@dataclass
class dataTransformationConfig():
    transformedData : str = os.path.join(os.getcwd(),"Artifacts","transformedData.csv")
    faissDB : str = os.path.join(os.getcwd(),"Artifacts")

class dataTransformation():
    def __init__(self):
        self.dataTransformationConfig = dataTransformationConfig()

    def intiate_data_transformation(self):
        try:
            logger.info("Starting Data Transformation")
            logger.info("Adding a random Price column in df")

            df= pd.read_json("/Users/sanketsaxena/Desktop/eccomChatbot/Artifacts/data/rawData.json")
            df['price'] = np.random.randint(10000, 45001, size=len(df))
            df['price']=df['price'].apply(lambda x : str(x))

            logger.info("Price Column Added")
            logger.info("Adding a full Description column in df")

            df['fullDescr'] = "Name: " + df['Phone'] + " Price: " + df['price']+ " Feature: " + df['Features'] 

            logger.info("Full Description column added")
            logger.info("Loading pandas dataFrame as langchain document")

            page_content_column = "fullDescr"
            loader = DataFrameLoader(df, page_content_column=page_content_column)
            docs = loader.load()

            logger.info("Loaded as document")
            logger.info("Converting documents as embeddings and storing them in FAISS DB")
            
            embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            faissDB = FAISS.from_documents(docs,embeddings)

            logger.info("Converted documents as embeddings and stored them in FAISS DB")
            logger.info("Saving transformed pandas df and faiss DB in Artifacts Folder")

            faissDB.save_local(folder_path=self.dataTransformationConfig.faissDB,index_name="faissDB")
            df.to_csv(self.dataTransformationConfig.transformedData)

            logger.info("Saved transformed pandas df and faiss DB in Artifacts Folder")

            return(
                self.dataTransformationConfig.faissDB,
                self.dataTransformationConfig.transformedData
            )
        except Exception as e:
            raise CustomException("Something is wrong in intiate_data_transformation method of dataTransformation class")