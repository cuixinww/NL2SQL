SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS meta DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
GRANT ALL PRIVILEGES ON meta.* TO 'nltosql'@'%';

USE meta;

DROP TABLE IF EXISTS table_info;
CREATE TABLE table_info
(
    id          VARCHAR(128) PRIMARY KEY COMMENT '表编号，格式 库名.表名',
    name        VARCHAR(128) COMMENT '表名称',
    table_type  VARCHAR(32) COMMENT '表类型(master/transaction/reference)',
    db_schema   VARCHAR(64) COMMENT '所属数据库',
    description TEXT COMMENT '表描述',
    alias       JSON COMMENT '表别名列表'
);

DROP TABLE IF EXISTS column_info;
CREATE TABLE column_info
(
    id             VARCHAR(128) PRIMARY KEY COMMENT '列编号',
    name           VARCHAR(128) COMMENT '列名称',
    data_type      VARCHAR(64) COMMENT '数据类型',
    role           VARCHAR(32) COMMENT '列类型(primary_key/foreign_key/attribute/measure)',
    examples       JSON COMMENT '数据示例',
    description    TEXT COMMENT '列描述',
    alias          JSON COMMENT '列别名',
    table_id       VARCHAR(128) COMMENT '所属表编号',
    ref_table_id   VARCHAR(128) DEFAULT '' COMMENT '外键引用目标表',
    ref_column_id  VARCHAR(128) DEFAULT '' COMMENT '外键引用目标列'
);

DROP TABLE IF EXISTS metric_info;
CREATE TABLE metric_info
(
    id               VARCHAR(64) PRIMARY KEY COMMENT '指标编码',
    name             VARCHAR(128) COMMENT '指标名称',
    description      TEXT COMMENT '指标描述',
    relevant_columns JSON COMMENT '关联的列',
    alias            JSON COMMENT '指标别名',
    formula          VARCHAR(256) DEFAULT '' COMMENT '聚合表达式',
    default_filter   VARCHAR(256) DEFAULT '' COMMENT '默认过滤条件'
);

DROP TABLE IF EXISTS table_relation;
CREATE TABLE table_relation
(
    id              VARCHAR(64) PRIMARY KEY COMMENT '关联编号',
    left_table_id   VARCHAR(128) COMMENT '左表编号',
    left_cols       JSON COMMENT '左表关联列',
    right_table_id  VARCHAR(128) COMMENT '右表编号',
    right_cols      JSON COMMENT '右表关联列',
    join_condition  VARCHAR(512) COMMENT 'JOIN 条件',
    is_preferred    TINYINT DEFAULT 0 COMMENT '是否首选路径',
    description     TEXT COMMENT '关联描述'
);
