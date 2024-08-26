CREATE MODEL `openai_embeddings`
INPUT (text STRING)
OUTPUT (embedding ARRAY<FLOAT>)
WITH(
  'TASK' = 'embedding',
  'PROVIDER' = 'OPENAI',
  'OPENAI.MODEL_VERSION' = 'text-embedding-ada-002',
  'OPENAI.ENDPOINT' = 'https://api.openai.com/v1/embeddings',
  'OPENAI.API_KEY' = '{{sessionconfig/sql.secrets.openaikey}}'
);