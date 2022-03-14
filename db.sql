drop table  if exists users
create table users(
    id integer primary key autoincrement,
    name string not null ,
    pwd string not null
)
