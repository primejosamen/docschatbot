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
# General
import json
import os
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
# initialize socketio client
sio = socketio.Client(logger=True, engineio_logger=True)
sio.sleep(0)
sio.connect('http://localhost:5001')
args = ccloud_lib.parse_args()
config_file = args.config_file
chatbotreqtopic = args.chatbotreqtopic
chatbotrestopic = args.chatbotrestopic
chatbotresfinaltopic = args.chatbotrestopicfinal
confconsumer = ccloud_lib.read_ccloud_config(config_file)
confproducer = ccloud_lib.read_ccloud_config(config_file)

schema_registry_conf = {
    "url": confconsumer["schema.registry.url"],
    "basic.auth.user.info": confconsumer["basic.auth.user.info"],
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
producer_conf = ""
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(confproducer)
delivered_records = 0
message_count = 0
waiting_count = 0
if __name__ == "__main__":
    # Read arguments and configurations and initialize
    args = ccloud_lib.parse_args()
    config_file = args.config_file
    chatbotrestopicfinal = args.chatbotrestopicfinal
    confconsumer = ccloud_lib.read_ccloud_config(config_file)
    confproducer = ccloud_lib.read_ccloud_config(config_file)

    schema_registry_conf = {
        "url": confconsumer["schema.registry.url"],
        "basic.auth.user.info": confconsumer["basic.auth.user.info"],
    }
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    chatbotresfinalvalue_avro_deserializer = AvroDeserializer(
        schema_registry_client=schema_registry_client,
        schema_str=ccloud_lib.chatbotres_final_value_schema,
        from_dict=ccloud_lib.Chatbotresfinalvalue.dict_to_chatbotresfinalvalue,
    )
    chatbotresfinalkey_avro_deserializer = AvroDeserializer(
        schema_registry_client=schema_registry_client,
        schema_str=ccloud_lib.chatbotres_final_key_schema,
        from_dict=ccloud_lib.Chatbotresfinalkey.dict_to_chatbotresfinalkey,
    )
    

    # for full list of configurations, see:
    #   https://docs.confluent.io/platform/current/clients/confluent-kafka-python/#deserializingconsumer
    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(confconsumer)
    consumer_conf["value.deserializer"] = chatbotresfinalvalue_avro_deserializer
    consumer_conf["key.deserializer"] = chatbotresfinalkey_avro_deserializer
    consumer = DeserializingConsumer(consumer_conf)
    
    # Subscribe to topic
    consumer.subscribe([chatbotresfinaltopic])



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
                chatbotresfinalvalue_object = msg.value()
                chatbotresfinalkey_object = msg.key()
                if chatbotresfinalvalue_object is not None:
                  answer = chatbotresfinalvalue_object.answer
                  funds_details = chatbotresfinalvalue_object.funds_current
                  reqid = chatbotresfinalkey_object.reqid
                  message_count = message_count + 1
                  if answer is not None:
                     print(
                           "Consumed record with value {}, Total processed rows {}".format(
                           answer, message_count
                          )
                     )
                  message_count = message_count + 1
                  message = (
                             "Search for information: "
                             + str(answer)
                             + " with genAI!"
                            )
                  # Here start with genAI
                  print("Hello LangChain!")
                  try:
                     # answer, sources = perform_question_answering(question)
                     # print(f"Question: {question}")
                     print("Answer:", answer,"funds_details:",funds_details)
                     sio.emit("data",{"answer":answer,"funds_details":funds_details,"reqid":reqid})
                     # publish_chatbotres(chatbotreq_object.query,chatbotreq_object.loginname,chatbotreq_object.context,chatbotreq_object.session_id,answer)
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
