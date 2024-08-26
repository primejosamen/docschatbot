INSERT INTO trades_data_v1
SELECT symbol,userid,total,price
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY symbol,userid ORDER BY $rowtime DESC) AS row_num
  FROM trades_realtime)
WHERE row_num <= 1