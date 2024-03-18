 create table disk_tree (
  id varchar primary key not null,
  url varchar,
  type varchar,
  size integer,
  full_route varchar,
  date timestamptz,
  parent_id varchar,
  foreign key (parent_id) references disk_tree(id) on delete cascade
);

create table node_history (
  id varchar,
  content jsonb,
  date timestamptz
);
