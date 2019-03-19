CREATE TABLE User(
    username INT PRIMARY KEY NOT NULL ,
    password VARCHAR(16) NOT NULL,
    stu_name VARCHAR(16) NOT NULL,
    stu_id VARCHAR(16) NOT NULL,
    stu_pwd VARCHAR(16) NOT NULL,
    stu_ip VARCHAR(16) NOT NULL
);

CREATE TABLE OperateLog(
    username INT NOT NULL,
    ts TIMESTAMP PRIMARY KEY NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operateType VARCHAR(16) NOT NULL ,
    sysTime VARCHAR(64) NOT NULL ,
    log VARCHAR(512)
);

CREATE TABLE LoginLog(
    username INT NOT NULL,
    ts TIMESTAMP PRIMARY KEY NOT NULL DEFAULT CURRENT_TIMESTAMP ,
    sysTime VARCHAR(64) NOT NULL,
    log VARCHAR(128)
);

SELECT username, password, stu_name, stu_id, stu_pwd, stu_ip FROM User WHERE username="" AND password="";

INSERT INTO LoginLog(username, sysTime, log) VALUES();
INSERT INTO OperateLog(username, operateType, sysTime, log) VALUES();