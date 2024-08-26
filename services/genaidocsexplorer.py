#!/usr/bin/env python
# =============================================================================
#
# Consume messages from Confluent Cloud
# Using Confluent Python Client for Apache Kafka
# Reads Avro data, integration with Confluent Cloud Schema Registry
# Call
# python icebreaker.py -f client.properties -t shoe_promotions
# avro consumer sample : https://github.com/confluentinc/examples/blob/7.5.0-post/clients/cloud/python/consumer_ccsr.py
# =============================================================================
# Confluent
import confluent_kafka
import uuid
import PyPDF2
from flask_socketio import SocketIO
from langchain_community.document_loaders import PyPDFLoader
from confluent_kafka import DeserializingConsumer
from confluent_kafka import SerializingProducer
from langchain.chains.conversation.memory import ConversationBufferMemory
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry.avro import AvroSerializer
#from confluent_kafka.schema_registry.avro import SerializerError
from confluent_kafka.avro.serializer import SerializerError
#from confluent_kafka.serialization import StringDeserializer
#from confluent_kafka.serialization import StringSerializer
from langchain.prompts import PromptTemplate
#from langchain_openai import OpenAI
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.agents import Tool
from langchain.chains import LLMChain
import ccloud_lib
import pymongo
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain import PromptTemplate
import requests
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from flask import Flask, request, jsonify, json
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.vectorstores import MongoDBAtlasVectorSearch
# AI
# General
import json
import os
from bson import json_util
app = Flask(__name__)
try:
    path = os.path.dirname(os.path.abspath(__file__))
    upload_folder=os.path.join(
    path.replace("/file_folder",""),"tmp")
    os.makedirs(upload_folder, exist_ok=True)
    app.config['upload_folder'] = upload_folder
except Exception as e:
    app.logger.info("An error occurred while creating temp folder")
    app.logger.error("Exception occurred : {}".format(e))
args = ccloud_lib.parse_args()
config_file = args.config_file
chatbotreqtopic = args.chatbotreqtopic
confproducer = ccloud_lib.read_ccloud_config(config_file)
confconsumer = ccloud_lib.read_ccloud_config(config_file)
schema_registry_conf = {
        "url": confconsumer["schema.registry.url"],
        "basic.auth.user.info": confconsumer["basic.auth.user.info"],
    }
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
# chatbotreq
chatbotreq_avro_serializer = AvroSerializer(
schema_registry_client = schema_registry_client,
schema_str =  ccloud_lib.chatbotreq_schema,
to_dict = ccloud_lib.Chatbotreq.chatbotreq_to_dict) 
# uploaddoc serializer
uploaddoc_avro_serializer = AvroSerializer(
schema_registry_client = schema_registry_client,
schema_str =  ccloud_lib.uploaddoc_schema,
to_dict = ccloud_lib.Uploaddoc.uploaddoc_to_dict)
# mongo connection
MONGO_URI = os.environ["MONGO_URI"]
client = pymongo.MongoClient(MONGO_URI)
db = client.genai
docscollection = db.docs_embeddings_v1
# chatcollection = db.chatbotreq
chatcollection = db.docs_chatbotres_step_final_v1
DB_NAME = "genai"
COLLECTION_NAME = "doc_embeddings"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"
# openai embedding
embedding_url = "https://api.openai.com/v1/embeddings"
# consumer
# for full list of configurations, see:
#   https://docs.confluent.io/platform/current/clients/confluent-kafka-python/#deserializingconsumer

message_count = 0
waiting_count = 0
# Subscribe to topic

# producer
producer_conf = ""
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(confproducer)
delivered_records = 0
# OpenAI init
# OPENAIKEY = os.environ["OPENAI_API_KEY"]
# llm = ChatOpenAI(model_name='gpt-3.5-turbo-1106',
#             temperature=0,
#             max_tokens = 256,response_format={ "type": "json_object" })
# Generate embeddings
llm = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)
# memory
memory = ConversationBufferMemory(
                memory_key="chat_history",
                input_key="question",
                output_key='answer',
                return_messages=True
            )
# semantic chunking
text_splitter = SemanticChunker(OpenAIEmbeddings())
char_text_splitter = CharacterTextSplitter(separator="\n\n",chunk_size=500, chunk_overlap=200,length_function=len,is_separator_regex=False,)
# mongo vector search
MONGO_URI = os.environ["MONGO_URI"]
# chat bot code
# Mongo RAG
def create_vector_search():
    """
    Creates a MongoDBAtlasVectorSearch object using the connection string, database, and collection names, along with the OpenAI embeddings and index configuration.
    """
    vector_search = MongoDBAtlasVectorSearch.from_connection_string(
        MONGO_URI,
        f"{DB_NAME}.{COLLECTION_NAME}",
        OpenAIEmbeddings(),
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME
    )
    return vector_search

def perform_question_answering(query):
    """
    This function uses a retriever and a language model to answer a query based on the context from documents.
    """
    vector_search = create_vector_search()

    # Setup the vector search as a retriever for finding similar documents
    qa_retriever_old = vector_search.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 100, "post_filter_pipeline": [{"$limit": 1}]}
    )
    qa_retriever = vector_search.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 100}
    ) 
    template = """
    Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question and also list the fund names and stock symbols mentioned in the answer:
    ------
    <ctx>
    {context}
    </ctx>
    ------
    <hs>
    {history}
    </hs>
    ------
    {question}
    Answer:
    """
    PROMPT = PromptTemplate(
        template=template, input_variables=["context", "chat_history","question"]
    )

    qa = RetrievalQA.from_chain_type(
        # llm=OpenAI(max_tokens=100),
        llm=llm,
        chain_type="stuff",
        retriever=qa_retriever,
        return_source_documents=True,
        chain_type_kwargs={
        "verbose": False,
        "prompt": PROMPT,
        "memory": ConversationBufferMemory(
            memory_key="history",
            input_key="question"),
        }
    )

    docs = qa({"query": query})

    return docs["result"], docs['source_documents']        
# query doc
@app.route("/jobportal/querydoc",methods=['POST'])
def query_docs():
      
    data= json.loads(request.data)
    print(data);
    jsondata = {}
    items = []
    userid = request.args.get('login')
    print(data["sessionid"])
    session_id = data["sessionid"]
    print(session_id)
    reqid = str(uuid.uuid4())
    question = data["searchquery"]
    context = str(data["context"])
    # answer, sources = perform_question_answering(question)
    print(f"Question: {question}")
    # print("Answer:", answer)
    # print("Source Documents:", sources)
    publish_chatbotreq(question,userid,reqid,context,session_id,"not yet formed")
    # return json_util.dumps({"airesponse":answer})
    return json_util.dumps({"reqid":reqid})
@app.route("/jobportal/recentqueries",methods=['GET'])
def usersearch_chatreq():
    login = request.args.get('login')
    print(login)
    chathisresult = {}
    chathisitems = []
    N = 3
    # chathis = chatcollection.find()
    chathis = chatcollection.aggregate([{ "$match" : {"loginname": login} }])
    # chathis = chatcollection.find()
    # print(searchhis)
    for document in list(chathis)[-N:]:
        print(json_util.dumps(document))
        chathisitems.append({'query': document["query"],"answer": document["answer"]})
    chathisresult['items'] = chathisitems
    # print(json_util.dumps(searchresult))
    return json_util.dumps(chathisresult)
# Publish job posting request
def publish_create_jobpost(jobreq,userid,reqid):
    try:
        def acked(err, msg):
                                global delivered_records
                                """
                                    Delivery report handler called on successful or failed delivery of message
                                """
                                if err is not None:
                                    print("Failed to deliver message: {}".format(err))
                                else:
                                    delivered_records += 1
                                    print("Produced record to topic {} partition [{}] @ offset {}"
                                        .format(msg.topic(), msg.partition(), msg.offset()))
        producer_conf["value.serializer"] = jobpost_avro_serializer
        producer = SerializingProducer(producer_conf)
        jobpost_object = ccloud_lib.Jobpost()
        jobpost_object.jobreq = jobreq
        jobpost_object.loginname = userid
        jobpost_object.reqid = reqid
        producer.produce(topic=jobposttopic, value=jobpost_object, on_delivery=acked)
        producer.poll(0)
        producer.flush()
    except Exception as e:
        print("An error occured:", e)
# Generate AI response
@app.route("/jobportal/aichat",methods=['POST'])
def generate_airesponse():
    login = request.args.get('login')
    postdata = json.loads(request.data)
    # print(llm.invoke(postdata['messages']))
    for msg in postdata['messages']:
      usertype=msg['type']
      message=msg['message']
      if usertype=='user':
        messages.append(("human",message))
      elif usertype=='bot':
        messages.append(("system",message))
    airesponse = llm.invoke(messages).content
    print(airesponse)
    data = {
            "airesponse" : airesponse
        }
    return jsonify(data);
@app.route("/jobportal/uploaddoc",methods=['POST'])
def upload_doc():
    file = request.files.get("file")
    userid = request.form.get("userid")
    print(userid)
    doc_name = file.filename
    save_path = os.path.join(
    app.config.get('upload_folder'),doc_name)
    file.save(save_path)
    id = str(uuid.uuid4())
    fhandle = open(save_path, 'rb')
    print(save_path)
    loader = PyPDFLoader(save_path)
    pages = loader.load_and_split()
    # pdfReader = PyPDF2.PdfReader(fhandle)
    # count = len(pdfReader.pages)
    for page in pages:
        partition_id = str(uuid.uuid4())
        publish_uploaddoc(page.metadata["source"],userid,page.metadata["page"],page.page_content,partition_id) 
    # for i in range(count):
        # docs = []
        # page = pdfReader.pages[i]
        # print(page.extract_text())
        # docs = text_splitter.create_documents([page.extract_text()])
        # docs = char_text_splitter.create_documents([page.extract_text()])
        # print(docs[0].page_content)
        # print(docs[0])
        # for doc in docs:
            # publish_uploaddoc(doc_name,userid,i,doc.page_content)--semantic split
            # publish_uploaddoc(doc_name,userid,i,doc)
            # partition_id = str(uuid.uuid4())
            # publish_uploaddoc(doc_name,userid+partition_id,i,doc.page_content)
    return id
# publish upload doc
def publish_uploaddoc(filename,userid,pagenum,content,chunk_id):
    try:
        def acked(err, msg):
                                global delivered_records
                                """
                                    Delivery report handler called on successful or failed delivery of message
                                """
                                if err is not None:
                                    print("Failed to deliver message: {}".format(err))
                                else:
                                    delivered_records += 1
                                    print("Produced record to topic {} partition [{}] @ offset {}"
                                        .format(msg.topic(), msg.partition(), msg.offset()))
        producer_conf["value.serializer"] = uploaddoc_avro_serializer
        producer = SerializingProducer(producer_conf)
        uploaddoc_object = ccloud_lib.Uploaddoc()
        uploaddoc_object.source = filename
        uploaddoc_object.loginname = userid
        uploaddoc_object.page = pagenum
        uploaddoc_object.text = content
        uploaddoc_object.chunk_id = chunk_id
        print(uploaddoc_object.loginname)
        print("i am here")
        producer.produce(topic="source_docs_v1", value=uploaddoc_object, on_delivery=acked)
        producer.poll(0)
        producer.flush()
    except Exception as e:
        print("An error occured:", e)
# publish upload doc
def publish_chatbotreq(query,userid,reqid,context,session_id,answer):
    try:
        def acked(err, msg):
                                global delivered_records
                                """
                                    Delivery report handler called on successful or failed delivery of message
                                """
                                if err is not None:
                                    print("Failed to deliver message: {}".format(err))
                                else:
                                    delivered_records += 1
                                    print("Produced record to topic {} partition [{}] @ offset {}"
                                        .format(msg.topic(), msg.partition(), msg.offset()))
        producer_conf["value.serializer"] = chatbotreq_avro_serializer
        producer = SerializingProducer(producer_conf)
        chatbotreq_object = ccloud_lib.Chatbotreq()
        chatbotreq_object.query = query
        chatbotreq_object.loginname = userid
        chatbotreq_object.reqid = reqid
        chatbotreq_object.context = context
        chatbotreq_object.session_id = session_id
        chatbotreq_object.answer = answer
        producer.produce(topic=chatbotreqtopic, value=chatbotreq_object, on_delivery=acked)
        producer.poll(0)
        producer.flush()
    except Exception as e:
        print("An error occured:", e)
if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
    # socket_io.run(app,debug=True,port=5001)
    # app.run(debug=True,port=5001)
