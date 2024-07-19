import os

from flask import Flask, request, jsonify,render_template


from src.logger import logger
from src.pipeline.rag_pipeline import ragPipeline

application = Flask(__name__)
app = application


os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

@app.route('/send-message', methods=["GET","POST"])
def send_message():
    if (request.method == "GET"):
        return render_template("chatbot.html")
    else:
        data = request.json
        session_id = data.get('session_id')
        user_message = data.get('message')
        rag_pipeline = ragPipeline()
        chain = rag_pipeline.initiatePipeline()
        
        
        config={"configurable": {"session_id": f"{session_id}"}}
        logger.info(f"{config['configurable']['session_id']}")
        # Process the query with your chatbot
        bot_reply = chain.invoke({"input": f"{user_message}"}, config=config)['answer']
        
        return jsonify({'reply': bot_reply})

if __name__ == '__main__':
    app.run(debug=True)
