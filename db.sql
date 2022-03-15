drop table if exists users
create table users
(
    id     integer primary key autoincrement,
    name   TEXT not null,
    pwd    TEXT not null,
    email  TEXT,
    label  TEXT,
    sex    int,
    remark TEXT
)
