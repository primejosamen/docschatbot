insert into docs_chatbotres_step_final
select
  docs_chatbotres_step_1.session_id,
  docs_chatbotres_step_1.reqid,
  docs_chatbotres_step_1.loginname,
  docs_chatbotres_step_1.query,
  docs_chatbotres_step_1.answer,
  ARRAY_AGG(ROW(trades_data_v1.symbol,trades_data_v1.price,trades_data_v1.total))
  from docs_chatbotres_step_1
INNER JOIN trades_data_v1 ON
docs_chatbotres_step_1.loginname = trades_data_v1.userid WHERE
docs_chatbotres_step_1.fundnames is not null
and POSITION(trades_data_v1.symbol in docs_chatbotres_step_1.fundnames) >0 GROUP BY
  docs_chatbotres_step_1.session_id,
  docs_chatbotres_step_1.reqid,
  docs_chatbotres_step_1.loginname,
  docs_chatbotres_step_1.query,
  docs_chatbotres_step_1.answer;