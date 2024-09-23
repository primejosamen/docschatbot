# genai-docsbot

A web portal that enables a GenAI chatbot experience on PDF documents allows users to interact with their documents through a generative AI-powered chatbot. This kind of portal is particularly useful in scenarios like legal document review, academic research, business reporting, and any other context where interacting with large volumes of text-based information is required.

This experience typically includes the following features:

1. **Data augmentation**:
   
![Data Augmentation flow](img/DataAugmentation.jpeg)
   
   * Users upload financial or account summary documents in PDF format.
   * The platform processes these documents by splitting them into individual pages and publishing each page's content, along with relevant metadata, to a Confluent Kafka topic.
   * A fully managed Confluent Flink service then generates vector representations of the document data and publishes these vector embeddings to another Confluent topic.
   * A fully managed Elastic sink connector reads the vector data from the topic and stores the vector embeddings. The documents are now prepared for chatbot queries.
   * Create search index on vector embeddings field in Elastic


2. **AI-Powered Interaction**: The portal is integrated with a generative AI model (like GPT) that can read, understand, and interact with the content of the documents. Users can ask the chatbot questions related to the document, request summaries, seek clarifications, or ask for specific sections or details. The AI can generate responses based on the content of the documents.
   
   Data Inference flow:
![Data Inference flow](img/DataInference.jpeg)

   * Users submits query through chatbot prompt, python microservice receives request on HTTP and generate an event to Confluent topic.
   * Python-Kafka consumer receives chatbot request, query vector store (Elastic) using vector search and pass the information to OpenAI to get an answer.
   * In the given answer, if there are any reference transactions mentioned, Confluent Flink enrich the answer using real time data from other private data sources.
   * Once the answer is fully enriched, A Python-Kafka consumer receives the final response from topic and sends to chatbot using websocket.
   * The final response is sinked to a data store to enable for analytical and auditing use cases.
   * If the user question is already answered, workflow query the datastore and respond back to the chatbot.

3. **Contextual Understanding**: The chatbot can understand the context of questions in relation to the document's content, making the interaction more meaningful and accurate. It can pull information, generate summaries, and provide insights based on the document's data.

## Demo-Video

## Demo Setup:

### Prerequisites
#### Tools
* install git to clone the source
  https://git-scm.com/book/it/v2/Per-Iniziare-Installing-Git
  ```
  yum install git
  ```
* install npm to install UI dependency packages (below example to install npm from yum package)
  ```
  yum install npm
  ```
* install python3
  ```
  yum install python3
  yum install --assumeyes python3-pip
  ```

#### Confluent Cloud

Demo:

You need a working account for Confluent Cloud. Sign-up with Confluent Cloud is very easy and you will get a $400 budget for your first trials for free. If you don't have a working Confluent Cloud account please [Sign-up to Confluent Cloud](https://www.confluent.io/confluent-cloud/tryfree/?utm_campaign=tm.campaigns_cd.Q124_EMEA_Stream-Processing-Essentials&utm_source=marketo&utm_medium=workshop).
=======
1. Sign up for a Confluent Cloud account [here](https://www.confluent.io/get-started/).
1. After verifying your email address, access Confluent Cloud sign-in by navigating [here](https://confluent.cloud).
1. When provided with the _username_ and _password_ prompts, fill in your credentials.

   > **Note:** If you're logging in for the first time you will see a wizard that will walk you through the some tutorials. Minimize this as you will walk through these steps in this guide.

1. Create Confluent Cloud API keys by following [this](https://registry.terraform.io/providers/confluentinc/confluent/latest/docs/guides/sample-project#summary) guide.
   > **Note:** This is different than Kafka cluster API keys.

#### Elastic Cloud

1. Sign up for a free Elastic account [here](https://www.elastic.co/cloud).

2. Reset password for `elastic` user in Elastic cloud cluster. Follow the instructions [here](https://www.elastic.co/guide/en/cloud-enterprise/current/ece-password-reset-elastic.html).
3. Get the elastic cloud id. Follow the instruction [here](https://www.elastic.co/search-labs/tutorials/install-elasticsearch/elastic-cloud).
   > **Note:** Elastic cloud id and password are needed for python service to connect

# Setup

1. Clone and enter this repository.

   ```bash
   git clone https://github.com/gopi0518/docschatbot.git
   cd docschatbot
   ```

1. Create an `.accounts` file by running the following command.

   ```bash
   echo "CONFLUENT_CLOUD_EMAIL=add_your_email\nCONFLUENT_CLOUD_PASSWORD=add_your_password\nexport TF_VAR_confluent_cloud_api_key=\"add_your_api_key\"\nexport TF_VAR_confluent_cloud_api_secret=\"add_your_api_secret\"" > .accounts

   ```

   > **Note:** This repo ignores `.accounts` file

1. Update the `.accounts` file for the following variables with your credentials.

   ```bash
   CONFLUENT_CLOUD_EMAIL=<replace>
   CONFLUENT_CLOUD_PASSWORD=<replace>
   export TF_VAR_confluent_cloud_api_key="<replace>"
   export TF_VAR_confluent_cloud_api_secret="<replace>"
   ```

1. Navigate to the home directory of the project and run `create_env.sh` script. This bash script copies the content of `.accounts` file into a new file called `.env` and append additional variables to it.

   ```bash
   ./create_env.sh
   ```

1. Source `.env` file.

   ```bash
   source .env
   ```

   > **Note:** if you don't source `.env` file you'll be prompted to manually provide the values through command line when running Terraform commands.
## Build your Confluent cloud infrastructure
1. Navigate to the repo's terraform directory.
```
cd terraform
```
2. Initialize Terraform within the directory.
```
terraform init
```
3. Create the Terraform plan.
```
terraform plan
```
4. Apply the plan to create the infrastructure.
```
terraform apply
```
5. Write the output of terraform to a JSON file. The setup.sh script will parse the JSON file to update the .env file.
```
terraform output -json > ../resources.json
```
## Run python services
Navigate to services directory and excute the remaining steps in this section

```
cd services
```
Install python modules

```
pip3 install PyPDF2
pip3 install gcc
pip3 install confluent-kafka
pip3 install langchain
pip3 install fastavro
pip3 install elasticsearch
pip3 install langchain_elasticsearch
pip3 install flask
pip3 install openai
pip3 install pyopenssl
pip3 install --quiet langchain_experimental
pip3 install flask_socketio
pip3 install flask_cors
pip3 install avro-python3
pip3 install jproperties

```
Set the env-vars

```
export OPENAI_API_KEY=<<OPEN_API_KEY>>
export ELASTIC_CLOUD=<<ELASTIC_CLOUD_ID>>
export ELASTIC_CLOUD_PASSWORD=<<ELASTIC_CLOUD_PASSWORD>>
```
Create client.properties file with Confluent connection parameters (this is needed for python services to run)
```
cat > client.properties
bootstrap.servers=<<confluent_cloud_bootstrap_url>>
security.protocol=SASL_SSL
sasl.mechanisms=PLAIN
sasl.username=<<CCLOUD_API_KEY>>
sasl.password=<<CCLOUD_API_SECRET>>
session.timeout.ms=45000
schema.registry.url=<<confluent_cloud_schema_registry>>
basic.auth.credentials.source=USER_INFO
basic.auth.user.info=<<SR_API_KEY>>:<<<<SR_API_SECRET>>
group.id=genai
auto.offset.reset=earliest
```
Run the python programs to receive data from UI and integrate with Confluent cloud
```
python3 server.py
python3 genaidocsexplorer.py -f client.properties -chatbotreq docs_chatbotreq_v1
python3 asyngenaichatres.py -f client.properties -chatbotresfinal docs_chatbotres_step_final_v1
python3 asyngenaichat.py -f client.properties -chatbotreq docs_chatbotreq_v1 -chatbotres docs_chatbotres_step_1 -chatbotresfinal docs_chatbotres_step_final_v1
```
## Run front-end code

Navigate to front-end

```
cd front-end
npm install
npm start
```
Go to browser try accessing UI: http://localhost:3000/




