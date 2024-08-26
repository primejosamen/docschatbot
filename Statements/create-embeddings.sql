create table doc_embeddings(
source STRING,
loginname STRING,
page INTEGER,
text STRING,
chunk_id STRING,
embedding ARRAY<DOUBLE NOT NULL>)