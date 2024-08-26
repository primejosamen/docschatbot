CREATE TABLE trades_data_v1 (
    symbol STRING,
    userid string,
    total double,
    price double,
    PRIMARY KEY(symbol,userid) NOT ENFORCED
);