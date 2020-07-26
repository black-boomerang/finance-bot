DROP TABLE IF EXISTS subscribers;

create table subscribers
(
    user_id integer not null constraint subscribers_pk primary key,
    user_name varchar default 'Уважаемый'::character varying not null,
    chat_id integer not null unique,
    recommendations boolean default true not null
);
