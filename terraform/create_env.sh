#!/bin/bash

accounts_file=".accounts"
env_file=".env"

# Check if .accounts file exists
if [ ! -f "$accounts_file" ]; then
    echo "$accounts_file not found."
    exit 1
fi

# Define the environment variable content
env_content=$(cat <<EOF
CCLOUD_API_KEY=NELWGHSLGNWSKAKH
CCLOUD_API_SECRET=cZc6ljuwy+pZ3V6ZkArR7KVNF8cD4HFIIiIIq+iMUZduF3n9n5q90SRS9j/qsY7W
CCLOUD_BOOTSTRAP_ENDPOINT=https://psrc-8kz20.us-east-2.aws.confluent.cloud

CCLOUD_SCHEMA_REGISTRY_API_KEY=sr-key
CCLOUD_SCHEMA_REGISTRY_API_SECRET=sr-secret
CCLOUD_SCHEMA_REGISTRY_URL=sr-cluster-endpoint

MONGO_USERNAME=admin
MONGO_PASSWORD=password123
MONGO_ENDPOINT=mongodb-endpoint
MONGO_DATABASE_NAME=mongodb-e5008c4210923563e43221c100866090cdffb5c95e7c97709703708f3d121232
EOF
)

# Combine the environment variable content with .accounts and write to .env
echo "$env_content" | cat - "$accounts_file" > "$env_file"

echo "Created an environment file named: $env_file"