from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.chains import create_history_aware_retriever,create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains.combine_documents import create_stuff_documents_chain

from src.utils import get_session_history
from src.exception import CustomException
from src.logger import logger

class ragPipeline():
    def __init__(self):
        pass

    def initiatePipeline(self):
        try:
            logger.info("Initializing our llm model")

            llm = ChatGroq(model= "Gemma2-9b-It")

            logger.info("Initialized our llm model")
            logger.info("Loading FAISS DB and getting retriever from it")

            embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            faissDB = FAISS.load_local(folder_path="/Users/sanketsaxena/Desktop/eccomChatbot/Artifacts",index_name="faissDB",embeddings=embeddings,allow_dangerous_deserialization=True)
            retriever = faissDB.as_retriever()

            logger.info("Loaded FAISS DB and got retriever from it")
            logger.info("Creating history aware retriever")

            contextualize_q_system_prompt = (
                "Given a chat history and the latest user question "
                "which might reference context in the chat history, "
                "formulate a standalone question which can be understood "
                "without the chat history. Do NOT answer the question, "
                "just reformulate it if needed and otherwise return it as is."
            )
            contextualize_q_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system",contextualize_q_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("user","{input}")
                ]
            )
            history_aware_retriever = create_history_aware_retriever(
                llm, retriever, contextualize_q_prompt
            )

            logger.info("Created history aware retriever")
            logger.info("Creating Prompt, Question_Answer_Chain, Rag_Chain")

            system_prompt = (
                """
                You are a helpful virtual assistant for a mobile e-commerce site called Sanket Mobile Store. Your goal is to assist users with the following based on context you are given:

                1. Welcome users and provide a friendly greeting.
                2. Help users browse the latest products.
                3. Assist users in finding specific items.
                4. Always give name of phones initially and then at last ask whether user wants more information about it. 
                6. Offer general assistance and answer questions.
                7. Connect users with customer support when needed.
                

                Remember to be friendly, helpful, and concise in your responses.

                Start with a greeting:
                "Hi there! 👋 Welcome to [Your Store Name]! I'm your virtual assistant, here to help you have a great shopping experience.\n How can I assist you today?"

                You can proceed with the conversation based on the user's input.
                """
                "\n\n"
                "{context}"
            )

            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system",system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("user","{input}")
                ]
            )
            question_and_answer_chain = create_stuff_documents_chain(llm,qa_prompt)
            rag_chain = create_retrieval_chain(history_aware_retriever,question_and_answer_chain)

            logger.info("Created Prompt, Question_Answer_Chain, Rag_Chain")
            logger.info("Initializing RunnableWithMessageHistory")

            conversational_rag_chain = RunnableWithMessageHistory(
                rag_chain,
                get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )

            logger.info("Initialized RunnableWithMessageHistory")

            return conversational_rag_chain

        except Exception as e:
            raise CustomException("Something is wrong in initiatePipeline method of ragPredictionPipeline class")