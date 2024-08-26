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
import socketio
import pymongo
import confluent_kafka
from confluent_kafka import DeserializingConsumer
from langchain.chains.conversation.memory import ConversationBufferMemory
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry.avro import AvroSerializer
#from confluent_kafka.serialization import StringDeserializer
#from confluent_kafka.serialization import StringSerializer
import ccloud_lib
# AI
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from linkedin import scrape_linkedin_profile
from linkedin_lookup_agent import lookup as linkedin_lookup_agent
#from tools.linkedin import scrape_linkedin_profile
#from tools.linkedin_lookup_agent import lookup as linkedin_lookup_agent
# General
import json
import os
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.vectorstores import MongoDBAtlasVectorSearch
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
OPENAIKEY = os.environ["OPENAI_API_KEY"]
# mongo connection
MONGO_URI = os.environ["MONGO_URI"]
client = pymongo.MongoClient(MONGO_URI)
db = client.genai
docscollection = db.docs_embeddings_v1
chatcollection = db.chatbotreq
DB_NAME = "genai"
COLLECTION_NAME = "doc_embeddings"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"
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
# initialize socketio client
# sio = socketio.Client(logger=True, engineio_logger=True)
# sio.connect('http://localhost:5001')
args = ccloud_lib.parse_args()
config_file = args.config_file
chatbotreqtopic = args.chatbotreqtopic
chatbotrestopic = args.chatbotrestopic
confconsumer = ccloud_lib.read_ccloud_config(config_file)
confproducer = ccloud_lib.read_ccloud_config(config_file)
chatbotrestopicfinal = args.chatbotrestopicfinal
schema_registry_conf = {
    "url": confconsumer["schema.registry.url"],
    "basic.auth.user.info": confconsumer["basic.auth.user.info"],
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
producer_conf = ""
chatbotres_producer_conf = ccloud_lib.pop_schema_registry_params_from_config(confproducer)
chatbotresfinal_producer_conf = ccloud_lib.pop_schema_registry_params_from_config(confproducer)
delivered_records = 0
fundnames = ""
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
message_count = 0
waiting_count = 0
# produce response
def publish_chatbotres(query,userid,reqid,context,session_id,answer):
    print("reached answer:",answer)
    chatbotres_avro_serializer = AvroSerializer(
    schema_registry_client = schema_registry_client,
    schema_str =  ccloud_lib.chatbotres_schema,
    to_dict = ccloud_lib.Chatbotres.chatbotres_to_dict)
    # Chatbot response final value
    chatbotresfinalkey_avro_serializer = AvroSerializer(
    schema_registry_client = schema_registry_client,
    schema_str =  ccloud_lib.chatbotres_final_key_schema,
    to_dict = ccloud_lib.Chatbotresfinalkey.chatbotresfinalkey_to_dict)
    # Chatbot response final key
    chatbotresfinalvalue_avro_serializer = AvroSerializer(
    schema_registry_client = schema_registry_client,
    schema_str =  ccloud_lib.chatbotres_final_value_schema,
    to_dict = ccloud_lib.Chatbotresfinalvalue.chatbotresfinalvalue_to_dict)
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
        chatbotres_producer_conf["value.serializer"] = chatbotres_avro_serializer
        chatbotresproducer = SerializingProducer(chatbotres_producer_conf)
        chatbotresfinal_producer_conf["value.serializer"] = chatbotresfinalvalue_avro_serializer
        chatbotresfinal_producer_conf["key.serializer"] = chatbotresfinalkey_avro_serializer
        chatbotresfinalproducer = SerializingProducer(chatbotresfinal_producer_conf)
        chatbotres_object = ccloud_lib.Chatbotres()
        chatbotresfinalvalue_object = ccloud_lib.Chatbotresfinalvalue()
        chatbotresfinalkey_object = ccloud_lib.Chatbotresfinalkey()
        print("reached?")
        if answer.find("I don't know")==-1:
           fundnames = answer.partition("Stock symbols")[2].strip()
        else:
           fundnames = "None"
        print(fundnames)
        if not (fundnames=="None") and (len(fundnames.strip())>0):
           print("reached this loop")
           print(fundnames)
           chatbotres_object.query = query
           chatbotres_object.loginname = userid
           chatbotres_object.reqid = reqid
           chatbotres_object.context = context
           chatbotres_object.session_id = session_id
           chatbotres_object.answer = answer
           chatbotres_object.fundnames = fundnames
           chatbotresproducer.produce(topic=chatbotrestopic, value=chatbotres_object, on_delivery=acked)
           chatbotresproducer.poll(0)
           chatbotresproducer.flush()
        else:
           chatbotresfinalvalue_object.loginname = userid
           chatbotresfinalvalue_object.query = query
           chatbotresfinalvalue_object.answer = answer
           chatbotresfinalkey_object.session_id = session_id
           chatbotresfinalkey_object.reqid = reqid
           chatbotresfinalproducer.produce(topic=chatbotrestopicfinal, key=chatbotresfinalkey_object,value=chatbotresfinalvalue_object, on_delivery=acked)
           chatbotresfinalproducer.poll(0)
           chatbotresfinalproducer.flush()
    except Exception as e:
        print("An error occured:", e)
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
    Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the user question.If you don't know the answer, just say that you don't know, don't try to make up an answer. If the answer is valid, from the answer, extract stock symbols:
    Desired format:
    Stock symbols: <comma_separated_list_of_stock_symbols>
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
if __name__ == "__main__":
    # Read arguments and configurations and initialize
    args = ccloud_lib.parse_args()
    config_file = args.config_file
    chatbotreqtopic = args.chatbotreqtopic
    confconsumer = ccloud_lib.read_ccloud_config(config_file)
    confproducer = ccloud_lib.read_ccloud_config(config_file)

    schema_registry_conf = {
        "url": confconsumer["schema.registry.url"],
        "basic.auth.user.info": confconsumer["basic.auth.user.info"],
    }
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    chatbotreq_avro_deserializer = AvroDeserializer(
        schema_registry_client=schema_registry_client,
        schema_str=ccloud_lib.chatbotreq_schema,
        from_dict=ccloud_lib.Chatbotreq.dict_to_chatbotreq,
    )

    # for full list of configurations, see:
    #   https://docs.confluent.io/platform/current/clients/confluent-kafka-python/#deserializingconsumer
    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(confconsumer)
    consumer_conf["value.deserializer"] = chatbotreq_avro_deserializer
    consumer = DeserializingConsumer(consumer_conf)
    
    # Subscribe to topic
    consumer.subscribe([chatbotreqtopic])



    # Process messages
    while True:
        try:
            msg = consumer.poll(1.0)
            if msg is None:
                # No message available within timeout.
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                waiting_count = waiting_count + 1
                print(
                    "{}. Waiting for message or event/error in poll(), Flink needs more data, that's why it take while to get 1 event".format(
                        waiting_count
                    )
                )
                continue
            elif msg.error():
                print("error: {}".format(msg.error()))
            else:
                message_count = 0
                chatbotreq_object = msg.value()
                if chatbotreq_object is not None:
                  question = chatbotreq_object.query
                  message_count = message_count + 1
                  if question is not None:
                     print(
                           "Consumed record with value {}, Total processed rows {}".format(
                           question, message_count
                          )
                     )
                  message_count = message_count + 1
                  message = (
                             "Search for information: "
                             + str(question)
                             + " with genAI!"
                            )
                  # Here start with genAI
                  print("Hello LangChain!")
                  try:
                     answer, sources = perform_question_answering(question)
                     print(f"Question: {question}")
                     print("Answer:", answer)
                     # sio.emit("data",answer)
                     publish_chatbotres(chatbotreq_object.query,chatbotreq_object.loginname,chatbotreq_object.reqid,chatbotreq_object.context,chatbotreq_object.session_id,answer)
                     # print("Source Documents:", sources)
                     # produce data back
                  except Exception as e:
                     print("An error occured:", e)
        except KeyboardInterrupt:
            break
        except SerializerError as e:
            # Report malformed record, discard results, continue polling
            print("Message deserialization failed {}".format(e))
            pass

    # Leave group and commit final offsets
    consumer.close()
