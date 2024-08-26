insert into doc_embeddings
       select `source`,
        loginname,
        page,
        text,
        chunk_id,
        embedding
        from source_docs_v1,LATERAL TABLE(ML_PREDICT('openai_embeddings', text))
        where text is not null;