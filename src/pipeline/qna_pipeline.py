from src.exception import CustomException
from src.logger import logger
from src.utils import generate_session_id

from src.pipeline.rag_pipeline import ragPipeline

class qnaPipeline():
    def __init__(self):
        pass

    def startQNA():
        try:
            rag_pipeline = ragPipeline()
            chain = rag_pipeline.initiatePipeline()
            config={"configurable": {"session_id": f"{generate_session_id()}"}}
        except Exception as e:
            raise CustomException("Something is wrong in startQNA method of qnaPipeline class")