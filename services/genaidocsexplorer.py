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
from langchain_community.document_loaders import PyPDFLoader
from confluent_kafka import DeserializingConsumer
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry.avro import AvroSerializer
#from confluent_kafka.schema_registry.avro import SerializerError
from confluent_kafka.avro.serializer import SerializerError
from langchain.utilities import GoogleSearchAPIWrapper
import ccloud_lib
import pymongo
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain import PromptTemplate
from elasticsearch import Elasticsearch
import requests
from flask import Flask, request, jsonify, json
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import CharacterTextSplitter
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
ELASTIC_PASSWORD = "<<ELASTIC_PASSWORD>>"

# Found in the 'Manage Deployment' page
CLOUD_ID = "<<CLOUD_ID>>"
client = Elasticsearch(cloud_id=CLOUD_ID,basic_auth=("elastic", ELASTIC_PASSWORD))

message_count = 0
waiting_count = 0
# Subscribe to topic

# producer
producer_conf = ""
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(confproducer)
delivered_records = 0
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
    chathis = client.search(index="test_index", query={"match": {"text": {"query": "I had chocalate chip pancakes and scrambled eggs for breakfast this morning."}}})
    # chathis = chatcollection.find()
    # chathis = chatcollection.aggregate([{ "$match" : {"loginname": login} }])
    # chathis = chatcollection.find()
    # print(searchhis)
    print(chathis["hits"]["hits"][0]["_source"]["text"])
    for document in list(chathis)[-N:]:
        print(json_util.dumps(document))
        # chathisitems.append({'query': document["query"],"answer": document["answer"]})
    chathisresult['items'] = chathisitems
    # print(json_util.dumps(searchresult))
    return json_util.dumps(chathisresult)
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
