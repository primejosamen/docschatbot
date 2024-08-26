create table docs_chatbotres_step_final
(session_id string,
reqid string,
loginname string,
query string,
answer string,
`funds_current` ARRAY < ROW <
    `fund_name` STRING,
    `price` double,
    `total` double
    > >, PRIMARY KEY(session_id,reqid) NOT ENFORCED)