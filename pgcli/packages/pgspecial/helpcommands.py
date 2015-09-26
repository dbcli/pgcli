helpcommands = {
    "ABORT": {
        "description": "Description\nABORT rolls back the current transaction and causes",
        "synopsis": "\nABORT [ WORK | TRANSACTION ]\n"
    },
    "ALLFILES": {
        "description": None,
        "synopsis": None
    },
    "ALTER AGGREGATE": {
        "description": "Description\nALTER AGGREGATE changes the definition of an",
        "synopsis": "\nALTER AGGREGATE name ( aggregate_signature ) RENAME TO new_name\nALTER AGGREGATE name ( aggregate_signature )\n                OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER AGGREGATE name ( aggregate_signature ) SET SCHEMA new_schema\nwhere aggregate_signature is:\n\n* |\n[ argmode ] [ argname ] argtype [ , ... ] |\n[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]\n"
    },
    "ALTER COLLATION": {
        "description": "Description\nALTER COLLATION changes the definition of a",
        "synopsis": "\nALTER COLLATION name RENAME TO new_name\nALTER COLLATION name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER COLLATION name SET SCHEMA new_schema\n"
    },
    "ALTER CONVERSION": {
        "description": "Description\nALTER CONVERSION changes the definition of a",
        "synopsis": "\nALTER CONVERSION name RENAME TO new_name\nALTER CONVERSION name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER CONVERSION name SET SCHEMA new_schema\n"
    },
    "ALTER DATABASE": {
        "description": "Description\nALTER DATABASE changes the attributes",
        "synopsis": "\nALTER DATABASE name [ [ WITH ] option [ ... ] ]\n\nwhere option can be:\n\n    ALLOW_CONNECTIONS allowconn\n    CONNECTION LIMIT connlimit\n    IS_TEMPLATE istemplate\n\nALTER DATABASE name RENAME TO new_name\n\nALTER DATABASE name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n\nALTER DATABASE name SET TABLESPACE new_tablespace\n\nALTER DATABASE name SET configuration_parameter { TO | = } { value | DEFAULT }\nALTER DATABASE name SET configuration_parameter FROM CURRENT\nALTER DATABASE name RESET configuration_parameter\nALTER DATABASE name RESET ALL\n"
    },
    "ALTER DEFAULT PRIVILEGES": {
        "description": "Description\nALTER DEFAULT PRIVILEGES allows you to set the privileges",
        "synopsis": "\nALTER DEFAULT PRIVILEGES\n    [ FOR { ROLE | USER } target_role [, ...] ]\n    [ IN SCHEMA schema_name [, ...] ]\n    abbreviated_grant_or_revoke\nwhere abbreviated_grant_or_revoke is one of:\n\nGRANT { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON TABLES\n    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]\n\nGRANT { { USAGE | SELECT | UPDATE }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON SEQUENCES\n    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]\n\nGRANT { EXECUTE | ALL [ PRIVILEGES ] }\n    ON FUNCTIONS\n    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]\n\nGRANT { USAGE | ALL [ PRIVILEGES ] }\n    ON TYPES\n    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON TABLES\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { USAGE | SELECT | UPDATE }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON SEQUENCES\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { EXECUTE | ALL [ PRIVILEGES ] }\n    ON FUNCTIONS\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON TYPES\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n"
    },
    "ALTER DOMAIN": {
        "description": "Description\nALTER DOMAIN changes the definition of an existing domain.",
        "synopsis": "\nALTER DOMAIN name\n    { SET DEFAULT expression | DROP DEFAULT }\nALTER DOMAIN name\n    { SET | DROP } NOT NULL\nALTER DOMAIN name\n    ADD domain_constraint [ NOT VALID ]\nALTER DOMAIN name\n    DROP CONSTRAINT [ IF EXISTS ] constraint_name [ RESTRICT | CASCADE ]\nALTER DOMAIN name\n     RENAME CONSTRAINT constraint_name TO new_constraint_name\nALTER DOMAIN name\n    VALIDATE CONSTRAINT constraint_name\nALTER DOMAIN name\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER DOMAIN name\n    RENAME TO new_name\nALTER DOMAIN name\n    SET SCHEMA new_schema\n"
    },
    "ALTER EVENT TRIGGER": {
        "description": "Description\nALTER EVENT TRIGGER changes properties of an",
        "synopsis": "\nALTER EVENT TRIGGER name DISABLE\nALTER EVENT TRIGGER name ENABLE [ REPLICA | ALWAYS ]\nALTER EVENT TRIGGER name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER EVENT TRIGGER name RENAME TO new_name\n"
    },
    "ALTER EXTENSION": {
        "description": "Description\nALTER EXTENSION changes the definition of an installed",
        "synopsis": "\nALTER EXTENSION name UPDATE [ TO new_version ]\nALTER EXTENSION name SET SCHEMA new_schema\nALTER EXTENSION name ADD member_object\nALTER EXTENSION name DROP member_object\nwhere member_object is:\n\n  AGGREGATE aggregate_name ( aggregate_signature ) |\n  CAST (source_type AS target_type) |\n  COLLATION object_name |\n  CONVERSION object_name |\n  DOMAIN object_name |\n  EVENT TRIGGER object_name |\n  FOREIGN DATA WRAPPER object_name |\n  FOREIGN TABLE object_name |\n  FUNCTION function_name ( [ [ argmode ] [ argname ] argtype [, ...] ] ) |\n  MATERIALIZED VIEW object_name |\n  OPERATOR operator_name (left_type, right_type) |\n  OPERATOR CLASS object_name USING index_method |\n  OPERATOR FAMILY object_name USING index_method |\n  [ PROCEDURAL ] LANGUAGE object_name |\n  SCHEMA object_name |\n  SEQUENCE object_name |\n  SERVER object_name |\n  TABLE object_name |\n  TEXT SEARCH CONFIGURATION object_name |\n  TEXT SEARCH DICTIONARY object_name |\n  TEXT SEARCH PARSER object_name |\n  TEXT SEARCH TEMPLATE object_name |\n  TRANSFORM FOR type_name LANGUAGE lang_name |\n  TYPE object_name |\n  VIEW object_name\nand aggregate_signature is:\n\n* |\n[ argmode ] [ argname ] argtype [ , ... ] |\n[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]\n"
    },
    "ALTER FOREIGN DATA WRAPPER": {
        "description": "Description\nALTER FOREIGN DATA WRAPPER changes the",
        "synopsis": "\nALTER FOREIGN DATA WRAPPER name\n    [ HANDLER handler_function | NO HANDLER ]\n    [ VALIDATOR validator_function | NO VALIDATOR ]\n    [ OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ]) ]\nALTER FOREIGN DATA WRAPPER name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER FOREIGN DATA WRAPPER name RENAME TO new_name\n"
    },
    "ALTER FOREIGN TABLE": {
        "description": "Description\nALTER FOREIGN TABLE changes the definition of an",
        "synopsis": "\nALTER FOREIGN TABLE [ IF EXISTS ] [ ONLY ] name [ * ]\n    action [, ... ]\nALTER FOREIGN TABLE [ IF EXISTS ] [ ONLY ] name [ * ]\n    RENAME [ COLUMN ] column_name TO new_column_name\nALTER FOREIGN TABLE [ IF EXISTS ] name\n    RENAME TO new_name\nALTER FOREIGN TABLE [ IF EXISTS ] name\n    SET SCHEMA new_schema\nwhere action is one of:\n\n    ADD [ COLUMN ] column_name data_type [ COLLATE collation ] [ column_constraint [ ... ] ]\n    DROP [ COLUMN ] [ IF EXISTS ] column_name [ RESTRICT | CASCADE ]\n    ALTER [ COLUMN ] column_name [ SET DATA ] TYPE data_type [ COLLATE collation ]\n    ALTER [ COLUMN ] column_name SET DEFAULT expression\n    ALTER [ COLUMN ] column_name DROP DEFAULT\n    ALTER [ COLUMN ] column_name { SET | DROP } NOT NULL\n    ALTER [ COLUMN ] column_name SET STATISTICS integer\n    ALTER [ COLUMN ] column_name SET ( attribute_option = value [, ... ] )\n    ALTER [ COLUMN ] column_name RESET ( attribute_option [, ... ] )\n    ALTER [ COLUMN ] column_name SET STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN }\n    ALTER [ COLUMN ] column_name OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ])\n    ADD table_constraint [ NOT VALID ]\n    VALIDATE CONSTRAINT constraint_name\n    DROP CONSTRAINT [ IF EXISTS ]  constraint_name [ RESTRICT | CASCADE ]\n    DISABLE TRIGGER [ trigger_name | ALL | USER ]\n    ENABLE TRIGGER [ trigger_name | ALL | USER ]\n    ENABLE REPLICA TRIGGER trigger_name\n    ENABLE ALWAYS TRIGGER trigger_name\n    SET WITH OIDS\n    SET WITHOUT OIDS\n    INHERIT parent_table\n    NO INHERIT parent_table\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n    OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ])\n"
    },
    "ALTER FUNCTION": {
        "description": "Description\nALTER FUNCTION changes the definition of a",
        "synopsis": "\nALTER FUNCTION name ( [ [ argmode ] [ argname ] argtype [, ...] ] )\n    action [ ... ] [ RESTRICT ]\nALTER FUNCTION name ( [ [ argmode ] [ argname ] argtype [, ...] ] )\n    RENAME TO new_name\nALTER FUNCTION name ( [ [ argmode ] [ argname ] argtype [, ...] ] )\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER FUNCTION name ( [ [ argmode ] [ argname ] argtype [, ...] ] )\n    SET SCHEMA new_schema\nwhere action is one of:\n\n    CALLED ON NULL INPUT | RETURNS NULL ON NULL INPUT | STRICT\n    IMMUTABLE | STABLE | VOLATILE | [ NOT ] LEAKPROOF\n    [ EXTERNAL ] SECURITY INVOKER | [ EXTERNAL ] SECURITY DEFINER\n    PARALLEL { UNSAFE | RESTRICTED | SAFE }\n    COST execution_cost\n    ROWS result_rows\n    SET configuration_parameter { TO | = } { value | DEFAULT }\n    SET configuration_parameter FROM CURRENT\n    RESET configuration_parameter\n    RESET ALL\n"
    },
    "ALTER GROUP": {
        "description": "Description\nALTER GROUP changes the attributes of a user group.",
        "synopsis": "\nALTER GROUP role_specification ADD USER user_name [, ... ]\nALTER GROUP role_specification DROP USER user_name [, ... ]\n\nwhere role_specification can be:\nrole_name\n  | CURRENT_USER\n  | SESSION_USER\n\nALTER GROUP group_name RENAME TO new_name\n"
    },
    "ALTER INDEX": {
        "description": "Description\nALTER INDEX changes the definition of an existing index.",
        "synopsis": "\nALTER INDEX [ IF EXISTS ] name RENAME TO new_name\nALTER INDEX [ IF EXISTS ] name SET TABLESPACE tablespace_name\nALTER INDEX [ IF EXISTS ] name SET ( storage_parameter = value [, ... ] )\nALTER INDEX [ IF EXISTS ] name RESET ( storage_parameter [, ... ] )\nALTER INDEX ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]\n    SET TABLESPACE new_tablespace [ NOWAIT ]\n"
    },
    "ALTER LANGUAGE": {
        "description": "Description\nALTER LANGUAGE changes the definition of a",
        "synopsis": "\nALTER [ PROCEDURAL ] LANGUAGE name RENAME TO new_name\nALTER [ PROCEDURAL ] LANGUAGE name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n"
    },
    "ALTER LARGE OBJECT": {
        "description": "Description\nALTER LARGE OBJECT changes the definition of a",
        "synopsis": "\nALTER LARGE OBJECT large_object_oid OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n"
    },
    "ALTER MATERIALIZED VIEW": {
        "description": "Description\nALTER MATERIALIZED VIEW changes various auxiliary",
        "synopsis": "\nALTER MATERIALIZED VIEW [ IF EXISTS ] name\naction [, ... ]\nALTER MATERIALIZED VIEW [ IF EXISTS ] name\n    RENAME [ COLUMN ] column_name TO new_column_name\nALTER MATERIALIZED VIEW [ IF EXISTS ] name\n    RENAME TO new_name\nALTER MATERIALIZED VIEW [ IF EXISTS ] name\n    SET SCHEMA new_schema\nALTER MATERIALIZED VIEW ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]\n    SET TABLESPACE new_tablespace [ NOWAIT ]\n\nwhere action is one of:\n\n    ALTER [ COLUMN ] column_name SET STATISTICS integer\n    ALTER [ COLUMN ] column_name SET ( attribute_option = value [, ... ] )\n    ALTER [ COLUMN ] column_name RESET ( attribute_option [, ... ] )\n    ALTER [ COLUMN ] column_name SET STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN }\n    CLUSTER ON index_name\n    SET WITHOUT CLUSTER\n    SET ( storage_parameter = value [, ... ] )\n    RESET ( storage_parameter [, ... ] )\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n    SET TABLESPACE new_tablespace\n"
    },
    "ALTER OPCLASS": {
        "description": "Description\nALTER OPERATOR CLASS changes the definition of",
        "synopsis": "\nALTER OPERATOR CLASS name USING index_method\n    RENAME TO new_name\n\nALTER OPERATOR CLASS name USING index_method\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n\nALTER OPERATOR CLASS name USING index_method\n    SET SCHEMA new_schema\n"
    },
    "ALTER OPERATOR": {
        "description": "Description\nALTER OPERATOR changes the definition of",
        "synopsis": "\nALTER OPERATOR name ( { left_type | NONE } , { right_type | NONE } )\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n\nALTER OPERATOR name ( { left_type | NONE } , { right_type | NONE } )\n    SET SCHEMA new_schema\n\nALTER OPERATOR name ( { left_type | NONE } , { right_type | NONE } )\n    SET ( {  RESTRICT = { res_proc | NONE }\n           | JOIN = { join_proc | NONE }\n         } [, ... ] )\n"
    },
    "ALTER OPFAMILY": {
        "description": "Description\nALTER OPERATOR FAMILY changes the definition of",
        "synopsis": "\nALTER OPERATOR FAMILY name USING index_method ADD\n  {  OPERATOR strategy_number operator_name ( op_type, op_type )\n              [ FOR SEARCH | FOR ORDER BY sort_family_name ]\n   | FUNCTION support_number [ ( op_type [ , op_type ] ) ]\n              function_name ( argument_type [, ...] )\n  } [, ... ]\n\nALTER OPERATOR FAMILY name USING index_method DROP\n  {  OPERATOR strategy_number ( op_type [ , op_type ] )\n   | FUNCTION support_number ( op_type [ , op_type ] )\n  } [, ... ]\n\nALTER OPERATOR FAMILY name USING index_method\n    RENAME TO new_name\n\nALTER OPERATOR FAMILY name USING index_method\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n\nALTER OPERATOR FAMILY name USING index_method\n    SET SCHEMA new_schema\n"
    },
    "ALTER POLICY": {
        "description": "Description\nALTER POLICY changes the ",
        "synopsis": "\nALTER POLICY name ON table_name\n    [ RENAME TO new_name ]\n    [ TO { role_name | PUBLIC | CURRENT_USER | SESSION_USER } [, ...] ]\n    [ USING ( using_expression ) ]\n    [ WITH CHECK ( check_expression ) ]\n"
    },
    "ALTER ROLE": {
        "description": "Description\nALTER ROLE changes the attributes of a",
        "synopsis": "\nALTER ROLE role_specification [ WITH ] option [ ... ]\n\nwhere option can be:\n\n      SUPERUSER | NOSUPERUSER\n    | CREATEDB | NOCREATEDB\n    | CREATEROLE | NOCREATEROLE\n    | CREATEUSER | NOCREATEUSER\n    | INHERIT | NOINHERIT\n    | LOGIN | NOLOGIN\n    | REPLICATION | NOREPLICATION\n    | BYPASSRLS | NOBYPASSRLS\n    | CONNECTION LIMIT connlimit\n    | [ ENCRYPTED | UNENCRYPTED ] PASSWORD 'password'\n    | VALID UNTIL 'timestamp'\n\nALTER ROLE name RENAME TO new_name\n\nALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter { TO | = } { value | DEFAULT }\nALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] SET configuration_parameter FROM CURRENT\nALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET configuration_parameter\nALTER ROLE { role_specification | ALL } [ IN DATABASE database_name ] RESET ALL\n\nwhere role_specification can be:\n\n    [ GROUP ] role_name\n  | CURRENT_USER\n  | SESSION_USER\n"
    },
    "ALTER RULE": {
        "description": "Description\nALTER RULE changes properties of an existing",
        "synopsis": "\nALTER RULE name ON table_name RENAME TO new_name\n"
    },
    "ALTER SCHEMA": {
        "description": "Description\nALTER SCHEMA changes the definition of a schema.",
        "synopsis": "\nALTER SCHEMA name RENAME TO new_name\nALTER SCHEMA name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n"
    },
    "ALTER SEQUENCE": {
        "description": "Description\nALTER SEQUENCE changes the parameters of an existing",
        "synopsis": "\nALTER SEQUENCE [ IF EXISTS ] name [ INCREMENT [ BY ] increment ]\n    [ MINVALUE minvalue | NO MINVALUE ] [ MAXVALUE maxvalue | NO MAXVALUE ]\n    [ START [ WITH ] start ]\n    [ RESTART [ [ WITH ] restart ] ]\n    [ CACHE cache ] [ [ NO ] CYCLE ]\n    [ OWNED BY { table_name.column_name | NONE } ]\nALTER SEQUENCE [ IF EXISTS ] name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER SEQUENCE [ IF EXISTS ] name RENAME TO new_name\nALTER SEQUENCE [ IF EXISTS ] name SET SCHEMA new_schema\n"
    },
    "ALTER SERVER": {
        "description": "Description\nALTER SERVER changes the definition of a foreign",
        "synopsis": "\nALTER SERVER name [ VERSION 'new_version' ]\n    [ OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] ) ]\nALTER SERVER name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER SERVER name RENAME TO new_name\n"
    },
    "ALTER SYSTEM": {
        "description": "Description\nALTER SYSTEM is used for changing server configuration",
        "synopsis": "\nALTER SYSTEM SET configuration_parameter { TO | = } { value | 'value' | DEFAULT }\n\nALTER SYSTEM RESET configuration_parameter\nALTER SYSTEM RESET ALL\n"
    },
    "ALTER TABLE": {
        "description": "Description\nALTER TABLE changes the definition of an existing table.",
        "synopsis": "\nALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]\n    action [, ... ]\nALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]\n    RENAME [ COLUMN ] column_name TO new_column_name\nALTER TABLE [ IF EXISTS ] [ ONLY ] name [ * ]\n    RENAME CONSTRAINT constraint_name TO new_constraint_name\nALTER TABLE [ IF EXISTS ] name\n    RENAME TO new_name\nALTER TABLE [ IF EXISTS ] name\n    SET SCHEMA new_schema\nALTER TABLE ALL IN TABLESPACE name [ OWNED BY role_name [, ... ] ]\n    SET TABLESPACE new_tablespace [ NOWAIT ]\n\nwhere action is one of:\n\n    ADD [ COLUMN ] [ IF NOT EXISTS ] column_name data_type [ COLLATE collation ] [ column_constraint [ ... ] ]\n    DROP [ COLUMN ] [ IF EXISTS ] column_name [ RESTRICT | CASCADE ]\n    ALTER [ COLUMN ] column_name [ SET DATA ] TYPE data_type [ COLLATE collation ] [ USING expression ]\n    ALTER [ COLUMN ] column_name SET DEFAULT expression\n    ALTER [ COLUMN ] column_name DROP DEFAULT\n    ALTER [ COLUMN ] column_name { SET | DROP } NOT NULL\n    ALTER [ COLUMN ] column_name SET STATISTICS integer\n    ALTER [ COLUMN ] column_name SET ( attribute_option = value [, ... ] )\n    ALTER [ COLUMN ] column_name RESET ( attribute_option [, ... ] )\n    ALTER [ COLUMN ] column_name SET STORAGE { PLAIN | EXTERNAL | EXTENDED | MAIN }\n    ADD table_constraint [ NOT VALID ]\n    ADD table_constraint_using_index\n    ALTER CONSTRAINT constraint_name [ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]\n    VALIDATE CONSTRAINT constraint_name\n    DROP CONSTRAINT [ IF EXISTS ]  constraint_name [ RESTRICT | CASCADE ]\n    DISABLE TRIGGER [ trigger_name | ALL | USER ]\n    ENABLE TRIGGER [ trigger_name | ALL | USER ]\n    ENABLE REPLICA TRIGGER trigger_name\n    ENABLE ALWAYS TRIGGER trigger_name\n    DISABLE RULE rewrite_rule_name\n    ENABLE RULE rewrite_rule_name\n    ENABLE REPLICA RULE rewrite_rule_name\n    ENABLE ALWAYS RULE rewrite_rule_name\n    DISABLE ROW LEVEL SECURITY\n    ENABLE ROW LEVEL SECURITY\n    CLUSTER ON index_name\n    SET WITHOUT CLUSTER\n    SET WITH OIDS\n    SET WITHOUT OIDS\n    SET TABLESPACE new_tablespace\n    SET { LOGGED | UNLOGGED }\n    SET ( storage_parameter = value [, ... ] )\n    RESET ( storage_parameter [, ... ] )\n    INHERIT parent_table\n    NO INHERIT parent_table\n    OF type_name\n    NOT OF\n    OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\n    REPLICA IDENTITY { DEFAULT | USING INDEX index_name | FULL | NOTHING }\n\nand table_constraint_using_index is:\n\n    [ CONSTRAINT constraint_name ]\n    { UNIQUE | PRIMARY KEY } USING INDEX index_name\n    [ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]\n"
    },
    "ALTER TABLESPACE": {
        "description": "Description\nALTER TABLESPACE can be used to change the definition of",
        "synopsis": "\nALTER TABLESPACE name RENAME TO new_name\nALTER TABLESPACE name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER TABLESPACE name SET ( tablespace_option = value [, ... ] )\nALTER TABLESPACE name RESET ( tablespace_option [, ... ] )\n"
    },
    "ALTER TRIGGER": {
        "description": "Description\nALTER TRIGGER changes properties of an existing",
        "synopsis": "\nALTER TRIGGER name ON table_name RENAME TO new_name\n"
    },
    "ALTER TSCONFIG": {
        "description": "Description\nALTER TEXT SEARCH CONFIGURATION changes the definition of",
        "synopsis": "\nALTER TEXT SEARCH CONFIGURATION name\n    ADD MAPPING FOR token_type [, ... ] WITH dictionary_name [, ... ]\nALTER TEXT SEARCH CONFIGURATION name\n    ALTER MAPPING FOR token_type [, ... ] WITH dictionary_name [, ... ]\nALTER TEXT SEARCH CONFIGURATION name\n    ALTER MAPPING REPLACE old_dictionary WITH new_dictionary\nALTER TEXT SEARCH CONFIGURATION name\n    ALTER MAPPING FOR token_type [, ... ] REPLACE old_dictionary WITH new_dictionary\nALTER TEXT SEARCH CONFIGURATION name\n    DROP MAPPING [ IF EXISTS ] FOR token_type [, ... ]\nALTER TEXT SEARCH CONFIGURATION name RENAME TO new_name\nALTER TEXT SEARCH CONFIGURATION name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER TEXT SEARCH CONFIGURATION name SET SCHEMA new_schema\n"
    },
    "ALTER TSDICTIONARY": {
        "description": "Description\nALTER TEXT SEARCH DICTIONARY changes the definition of",
        "synopsis": "\nALTER TEXT SEARCH DICTIONARY name (\n    option [ = value ] [, ... ]\n)\nALTER TEXT SEARCH DICTIONARY name RENAME TO new_name\nALTER TEXT SEARCH DICTIONARY name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER TEXT SEARCH DICTIONARY name SET SCHEMA new_schema\n"
    },
    "ALTER TSPARSER": {
        "description": "Description\nALTER TEXT SEARCH PARSER changes the definition of",
        "synopsis": "\nALTER TEXT SEARCH PARSER name RENAME TO new_name\nALTER TEXT SEARCH PARSER name SET SCHEMA new_schema\n"
    },
    "ALTER TSTEMPLATE": {
        "description": "Description\nALTER TEXT SEARCH TEMPLATE changes the definition of",
        "synopsis": "\nALTER TEXT SEARCH TEMPLATE name RENAME TO new_name\nALTER TEXT SEARCH TEMPLATE name SET SCHEMA new_schema\n"
    },
    "ALTER TYPE": {
        "description": "Description\nALTER TYPE changes the definition of an existing type.",
        "synopsis": "\nALTER TYPE name action [, ... ]\nALTER TYPE name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER TYPE name RENAME ATTRIBUTE attribute_name TO new_attribute_name [ CASCADE | RESTRICT ]\nALTER TYPE name RENAME TO new_name\nALTER TYPE name SET SCHEMA new_schema\nALTER TYPE name ADD VALUE [ IF NOT EXISTS ] new_enum_value [ { BEFORE | AFTER } existing_enum_value ]\n\nwhere action is one of:\n\n    ADD ATTRIBUTE attribute_name data_type [ COLLATE collation ] [ CASCADE | RESTRICT ]\n    DROP ATTRIBUTE [ IF EXISTS ] attribute_name [ CASCADE | RESTRICT ]\n    ALTER ATTRIBUTE attribute_name [ SET DATA ] TYPE data_type [ COLLATE collation ] [ CASCADE | RESTRICT ]\n"
    },
    "ALTER USER": {
        "description": "Description\nALTER USER is now an alias for",
        "synopsis": "\nALTER USER role_specification [ WITH ] option [ ... ]\n\nwhere option can be:\n\n      SUPERUSER | NOSUPERUSER\n    | CREATEDB | NOCREATEDB\n    | CREATEROLE | NOCREATEROLE\n    | CREATEUSER | NOCREATEUSER\n    | INHERIT | NOINHERIT\n    | LOGIN | NOLOGIN\n    | REPLICATION | NOREPLICATION\n    | CONNECTION LIMIT connlimit\n    | [ ENCRYPTED | UNENCRYPTED ] PASSWORD 'password'\n    | VALID UNTIL 'timestamp'\n\nALTER USER name RENAME TO new_name\n\nALTER USER role_specification SET configuration_parameter { TO | = } { value | DEFAULT }\nALTER USER role_specification SET configuration_parameter FROM CURRENT\nALTER USER role_specification RESET configuration_parameter\nALTER USER role_specification RESET ALL\n\nwhere role_specification can be:\n\n    [ GROUP ] role_name\n  | CURRENT_USER\n  | SESSION_USER\n"
    },
    "ALTER USER MAPPING": {
        "description": "Description\nALTER USER MAPPING changes the definition of a",
        "synopsis": "\nALTER USER MAPPING FOR { user_name | USER | CURRENT_USER | SESSION_USER | PUBLIC }\n    SERVER server_name\n    OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] )\n"
    },
    "ALTER VIEW": {
        "description": "Description\nALTER VIEW changes various auxiliary properties",
        "synopsis": "\nALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] column_name SET DEFAULT expression\nALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] column_name DROP DEFAULT\nALTER VIEW [ IF EXISTS ] name OWNER TO { new_owner | CURRENT_USER | SESSION_USER }\nALTER VIEW [ IF EXISTS ] name RENAME TO new_name\nALTER VIEW [ IF EXISTS ] name SET SCHEMA new_schema\nALTER VIEW [ IF EXISTS ] name SET ( view_option_name [= view_option_value] [, ... ] )\nALTER VIEW [ IF EXISTS ] name RESET ( view_option_name [, ... ] )\n"
    },
    "ANALYZE": {
        "description": "Description\nANALYZE collects statistics about the contents",
        "synopsis": "\nANALYZE [ VERBOSE ] [ table_name [ ( column_name [, ...] ) ] ]\n"
    },
    "BEGIN": {
        "description": "Description\nBEGIN initiates a transaction block, that is,",
        "synopsis": "\nBEGIN [ WORK | TRANSACTION ] [ transaction_mode [, ...] ]\n\nwhere transaction_mode is one of:\n\n    ISOLATION LEVEL { SERIALIZABLE | REPEATABLE READ | READ COMMITTED | READ UNCOMMITTED }\n    READ WRITE | READ ONLY\n    [ NOT ] DEFERRABLE\n"
    },
    "CHECKPOINT": {
        "description": "Description\n   A checkpoint is a point in the transaction log sequence at which",
        "synopsis": "\nCHECKPOINT\n"
    },
    "CLOSE": {
        "description": "Description\nCLOSE frees the resources associated with an open cursor.",
        "synopsis": "\nCLOSE { name | ALL }\n"
    },
    "CLUSTER": {
        "description": "Description\nCLUSTER instructs PostgreSQL",
        "synopsis": "\nCLUSTER [VERBOSE] table_name [ USING index_name ]\nCLUSTER [VERBOSE]\n"
    },
    "CLUSTERDB": {
        "description": "Description\nclusterdb is a utility for reclustering tables",
        "synopsis": None
    },
    "COMMENT": {
        "description": "Description\nCOMMENT stores a comment about a database object.",
        "synopsis": "\nCOMMENT ON\n{\n  AGGREGATE aggregate_name ( aggregate_signature ) |\n  CAST (source_type AS target_type) |\n  COLLATION object_name |\n  COLUMN relation_name.column_name |\n  CONSTRAINT constraint_name ON table_name |\n  CONSTRAINT constraint_name ON DOMAIN domain_name |\n  CONVERSION object_name |\n  DATABASE object_name |\n  DOMAIN object_name |\n  EXTENSION object_name |\n  EVENT TRIGGER object_name |\n  FOREIGN DATA WRAPPER object_name |\n  FOREIGN TABLE object_name |\n  FUNCTION function_name ( [ [ argmode ] [ argname ] argtype [, ...] ] ) |\n  INDEX object_name |\n  LARGE OBJECT large_object_oid |\n  MATERIALIZED VIEW object_name |\n  OPERATOR operator_name (left_type, right_type) |\n  OPERATOR CLASS object_name USING index_method |\n  OPERATOR FAMILY object_name USING index_method |\n  POLICY policy_name ON table_name |\n  [ PROCEDURAL ] LANGUAGE object_name |\n  ROLE object_name |\n  RULE rule_name ON table_name |\n  SCHEMA object_name |\n  SEQUENCE object_name |\n  SERVER object_name |\n  TABLE object_name |\n  TABLESPACE object_name |\n  TEXT SEARCH CONFIGURATION object_name |\n  TEXT SEARCH DICTIONARY object_name |\n  TEXT SEARCH PARSER object_name |\n  TEXT SEARCH TEMPLATE object_name |\n  TRANSFORM FOR type_name LANGUAGE lang_name |\n  TRIGGER trigger_name ON table_name |\n  TYPE object_name |\n  VIEW object_name\n} IS 'text'\n\nwhere aggregate_signature is:\n\n* |\n[ argmode ] [ argname ] argtype [ , ... ] |\n[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]\n"
    },
    "COMMIT": {
        "description": "Description\nCOMMIT commits the current transaction. All",
        "synopsis": "\nCOMMIT [ WORK | TRANSACTION ]\n"
    },
    "COMMIT PREPARED": {
        "description": "Description\nCOMMIT PREPARED commits a transaction that is in",
        "synopsis": "\nCOMMIT PREPARED transaction_id\n"
    },
    "COPY": {
        "description": "Description\nCOPY moves data between",
        "synopsis": "\nCOPY table_name [ ( column_name [, ...] ) ]\n    FROM { 'filename' | PROGRAM 'command' | STDIN }\n    [ [ WITH ] ( option [, ...] ) ]\n\nCOPY { table_name [ ( column_name [, ...] ) ] | ( query ) }\n    TO { 'filename' | PROGRAM 'command' | STDOUT }\n    [ [ WITH ] ( option [, ...] ) ]\n\nwhere option can be one of:\n\n    FORMAT format_name\n    OIDS [ boolean ]\n    FREEZE [ boolean ]\n    DELIMITER 'delimiter_character'\n    NULL 'null_string'\n    HEADER [ boolean ]\n    QUOTE 'quote_character'\n    ESCAPE 'escape_character'\n    FORCE_QUOTE { ( column_name [, ...] ) | * }\n    FORCE_NOT_NULL ( column_name [, ...] )\n    FORCE_NULL ( column_name [, ...] )\n    ENCODING 'encoding_name'\n"
    },
    "CREATE AGGREGATE": {
        "description": "Description\nCREATE AGGREGATE defines a new aggregate",
        "synopsis": "\nCREATE AGGREGATE name ( [ argmode ] [ argname ] arg_data_type [ , ... ] ) (\n    SFUNC = sfunc,\n    STYPE = state_data_type\n    [ , SSPACE = state_data_size ]\n    [ , FINALFUNC = ffunc ]\n    [ , FINALFUNC_EXTRA ]\n    [ , INITCOND = initial_condition ]\n    [ , MSFUNC = msfunc ]\n    [ , MINVFUNC = minvfunc ]\n    [ , MSTYPE = mstate_data_type ]\n    [ , MSSPACE = mstate_data_size ]\n    [ , MFINALFUNC = mffunc ]\n    [ , MFINALFUNC_EXTRA ]\n    [ , MINITCOND = minitial_condition ]\n    [ , SORTOP = sort_operator ]\n)\n\nCREATE AGGREGATE name ( [ [ argmode ] [ argname ] arg_data_type [ , ... ] ]\n                        ORDER BY [ argmode ] [ argname ] arg_data_type [ , ... ] ) (\n    SFUNC = sfunc,\n    STYPE = state_data_type\n    [ , SSPACE = state_data_size ]\n    [ , FINALFUNC = ffunc ]\n    [ , FINALFUNC_EXTRA ]\n    [ , INITCOND = initial_condition ]\n    [ , HYPOTHETICAL ]\n)\n\nor the old syntax\n\nCREATE AGGREGATE name (\n    BASETYPE = base_type,\n    SFUNC = sfunc,\n    STYPE = state_data_type\n    [ , SSPACE = state_data_size ]\n    [ , FINALFUNC = ffunc ]\n    [ , FINALFUNC_EXTRA ]\n    [ , INITCOND = initial_condition ]\n    [ , MSFUNC = msfunc ]\n    [ , MINVFUNC = minvfunc ]\n    [ , MSTYPE = mstate_data_type ]\n    [ , MSSPACE = mstate_data_size ]\n    [ , MFINALFUNC = mffunc ]\n    [ , MFINALFUNC_EXTRA ]\n    [ , MINITCOND = minitial_condition ]\n    [ , SORTOP = sort_operator ]\n)\n"
    },
    "CREATE CAST": {
        "description": "Description\nCREATE CAST defines a new cast.  A cast",
        "synopsis": "\nCREATE CAST (source_type AS target_type)\n    WITH FUNCTION function_name (argument_type [, ...])\n    [ AS ASSIGNMENT | AS IMPLICIT ]\n\nCREATE CAST (source_type AS target_type)\n    WITHOUT FUNCTION\n    [ AS ASSIGNMENT | AS IMPLICIT ]\n\nCREATE CAST (source_type AS target_type)\n    WITH INOUT\n    [ AS ASSIGNMENT | AS IMPLICIT ]\n"
    },
    "CREATE COLLATION": {
        "description": "Description\nCREATE COLLATION defines a new collation using",
        "synopsis": "\nCREATE COLLATION name (\n    [ LOCALE = locale, ]\n    [ LC_COLLATE = lc_collate, ]\n    [ LC_CTYPE = lc_ctype ]\n)\nCREATE COLLATION name FROM existing_collation\n"
    },
    "CREATE CONVERSION": {
        "description": "Description\nCREATE CONVERSION defines a new conversion between",
        "synopsis": "\nCREATE [ DEFAULT ] CONVERSION name\n    FOR source_encoding TO dest_encoding FROM function_name\n"
    },
    "CREATE DATABASE": {
        "description": "Description\nCREATE DATABASE creates a new",
        "synopsis": "\nCREATE DATABASE name\n    [ [ WITH ] [ OWNER [=] user_name ]\n           [ TEMPLATE [=] template ]\n           [ ENCODING [=] encoding ]\n           [ LC_COLLATE [=] lc_collate ]\n           [ LC_CTYPE [=] lc_ctype ]\n           [ TABLESPACE [=] tablespace_name ]\n           [ ALLOW_CONNECTIONS [=] allowconn ]\n           [ CONNECTION LIMIT [=] connlimit ] ]\n           [ IS_TEMPLATE [=] istemplate ]\n"
    },
    "CREATE DOMAIN": {
        "description": "Description\nCREATE DOMAIN creates a new domain.  A domain is",
        "synopsis": "\nCREATE DOMAIN name [ AS ] data_type\n    [ COLLATE collation ]\n    [ DEFAULT expression ]\n    [ constraint [ ... ] ]\n\nwhere constraint is:\n\n[ CONSTRAINT constraint_name ]\n{ NOT NULL | NULL | CHECK (expression) }\n"
    },
    "CREATE EVENT TRIGGER": {
        "description": "Description\nCREATE EVENT TRIGGER creates a new event trigger.",
        "synopsis": "\nCREATE EVENT TRIGGER name\n    ON event\n    [ WHEN filter_variable IN (filter_value [, ... ]) [ AND ... ] ]\n    EXECUTE PROCEDURE function_name()\n"
    },
    "CREATE EXTENSION": {
        "description": "Description\nCREATE EXTENSION loads a new extension into the current",
        "synopsis": "\nCREATE EXTENSION [ IF NOT EXISTS ] extension_name\n    [ WITH ] [ SCHEMA schema_name ]\n             [ VERSION version ]\n             [ FROM old_version ]\n"
    },
    "CREATE FOREIGN DATA WRAPPER": {
        "description": "Description\nCREATE FOREIGN DATA WRAPPER creates a new",
        "synopsis": "\nCREATE FOREIGN DATA WRAPPER name\n    [ HANDLER handler_function | NO HANDLER ]\n    [ VALIDATOR validator_function | NO VALIDATOR ]\n    [ OPTIONS ( option 'value' [, ... ] ) ]\n"
    },
    "CREATE FOREIGN TABLE": {
        "description": "Description\nCREATE FOREIGN TABLE creates a new foreign table",
        "synopsis": "\nCREATE FOREIGN TABLE [ IF NOT EXISTS ] table_name ( [\n  { column_name data_type [ OPTIONS ( option 'value' [, ... ] ) ] [ COLLATE collation ] [ column_constraint [ ... ] ]\n    | table_constraint }\n    [, ... ]\n] )\n[ INHERITS ( parent_table [, ... ] ) ]\n  SERVER server_name\n[ OPTIONS ( option 'value' [, ... ] ) ]\n\nwhere column_constraint is:\n\n[ CONSTRAINT constraint_name ]\n{ NOT NULL |\n  NULL |\n  CHECK ( expression ) [ NO INHERIT ] |\n  DEFAULT default_expr }\n\nand table_constraint is:\n\n[ CONSTRAINT constraint_name ]\nCHECK ( expression ) [ NO INHERIT ]\n"
    },
    "CREATE FUNCTION": {
        "description": "Description\nCREATE FUNCTION defines a new function.",
        "synopsis": "\nCREATE [ OR REPLACE ] FUNCTION\n    name ( [ [ argmode ] [ argname ] argtype [ { DEFAULT | = } default_expr ] [, ...] ] )\n    [ RETURNS rettype\n      | RETURNS TABLE ( column_name column_type [, ...] ) ]\n  { LANGUAGE lang_name\n    | TRANSFORM { FOR TYPE type_name } [, ... ]\n    | WINDOW\n    | IMMUTABLE | STABLE | VOLATILE | [ NOT ] LEAKPROOF\n    | CALLED ON NULL INPUT | RETURNS NULL ON NULL INPUT | STRICT\n    | [ EXTERNAL ] SECURITY INVOKER | [ EXTERNAL ] SECURITY DEFINER\n    | PARALLEL { UNSAFE | RESTRICTED | SAFE }\n    | COST execution_cost\n    | ROWS result_rows\n    | SET configuration_parameter { TO value | = value | FROM CURRENT }\n    | AS 'definition'\n    | AS 'obj_file', 'link_symbol'\n  } ...\n    [ WITH ( attribute [, ...] ) ]\n"
    },
    "CREATE GROUP": {
        "description": "Description\nCREATE GROUP is now an alias for",
        "synopsis": "\nCREATE GROUP name [ [ WITH ] option [ ... ] ]\n\nwhere option can be:\n\n      SUPERUSER | NOSUPERUSER\n    | CREATEDB | NOCREATEDB\n    | CREATEROLE | NOCREATEROLE\n    | CREATEUSER | NOCREATEUSER\n    | INHERIT | NOINHERIT\n    | LOGIN | NOLOGIN\n    | [ ENCRYPTED | UNENCRYPTED ] PASSWORD 'password'\n    | VALID UNTIL 'timestamp'\n    | IN ROLE role_name [, ...]\n    | IN GROUP role_name [, ...]\n    | ROLE role_name [, ...]\n    | ADMIN role_name [, ...]\n    | USER role_name [, ...]\n    | SYSID uid\n"
    },
    "CREATE INDEX": {
        "description": "Description\nCREATE INDEX constructs an index on the specified column(s)",
        "synopsis": "\nCREATE [ UNIQUE ] INDEX [ CONCURRENTLY ] [ [ IF NOT EXISTS ] name ] ON table_name [ USING method ]\n    ( { column_name | ( expression ) } [ COLLATE collation ] [ opclass ] [ ASC | DESC ] [ NULLS { FIRST | LAST } ] [, ...] )\n    [ WITH ( storage_parameter = value [, ... ] ) ]\n    [ TABLESPACE tablespace_name ]\n    [ WHERE predicate ]\n"
    },
    "CREATE LANGUAGE": {
        "description": "Description\nCREATE LANGUAGE registers a new",
        "synopsis": "\nCREATE [ OR REPLACE ] [ PROCEDURAL ] LANGUAGE name\nCREATE [ OR REPLACE ] [ TRUSTED ] [ PROCEDURAL ] LANGUAGE name\n    HANDLER call_handler [ INLINE inline_handler ] [ VALIDATOR valfunction ]\n"
    },
    "CREATE MATERIALIZED VIEW": {
        "description": "Description\nCREATE MATERIALIZED VIEW defines a materialized view of",
        "synopsis": "\nCREATE MATERIALIZED VIEW [ IF NOT EXISTS ] table_name\n    [ (column_name [, ...] ) ]\n    [ WITH ( storage_parameter [= value] [, ... ] ) ]\n    [ TABLESPACE tablespace_name ]\n    AS query\n    [ WITH [ NO ] DATA ]\n"
    },
    "CREATE OPCLASS": {
        "description": "Description\nCREATE OPERATOR CLASS creates a new operator class.",
        "synopsis": "\nCREATE OPERATOR CLASS name [ DEFAULT ] FOR TYPE data_type\n  USING index_method [ FAMILY family_name ] AS\n  {  OPERATOR strategy_number operator_name [ ( op_type, op_type ) ] [ FOR SEARCH | FOR ORDER BY sort_family_name ]\n   | FUNCTION support_number [ ( op_type [ , op_type ] ) ] function_name ( argument_type [, ...] )\n   | STORAGE storage_type\n  } [, ... ]\n"
    },
    "CREATE OPERATOR": {
        "description": "Description\nCREATE OPERATOR defines a new operator,",
        "synopsis": "\nCREATE OPERATOR name (\n    PROCEDURE = function_name\n    [, LEFTARG = left_type ] [, RIGHTARG = right_type ]\n    [, COMMUTATOR = com_op ] [, NEGATOR = neg_op ]\n    [, RESTRICT = res_proc ] [, JOIN = join_proc ]\n    [, HASHES ] [, MERGES ]\n)\n"
    },
    "CREATE OPFAMILY": {
        "description": "Description\nCREATE OPERATOR FAMILY creates a new operator family.",
        "synopsis": "\nCREATE OPERATOR FAMILY name USING index_method\n"
    },
    "CREATE POLICY": {
        "description": "Description\n   The CREATE POLICY command defines a new policy for a",
        "synopsis": "\nCREATE POLICY name ON table_name\n    [ FOR { ALL | SELECT | INSERT | UPDATE | DELETE } ]\n    [ TO { role_name | PUBLIC | CURRENT_USER | SESSION_USER } [, ...] ]\n    [ USING ( using_expression ) ]\n    [ WITH CHECK ( check_expression ) ]\n"
    },
    "CREATE ROLE": {
        "description": "Description\nCREATE ROLE adds a new role to a",
        "synopsis": "\nCREATE ROLE name [ [ WITH ] option [ ... ] ]\n\nwhere option can be:\n\n      SUPERUSER | NOSUPERUSER\n    | CREATEDB | NOCREATEDB\n    | CREATEROLE | NOCREATEROLE\n    | CREATEUSER | NOCREATEUSER\n    | INHERIT | NOINHERIT\n    | LOGIN | NOLOGIN\n    | REPLICATION | NOREPLICATION\n    | BYPASSRLS | NOBYPASSRLS\n    | CONNECTION LIMIT connlimit\n    | [ ENCRYPTED | UNENCRYPTED ] PASSWORD 'password'\n    | VALID UNTIL 'timestamp'\n    | IN ROLE role_name [, ...]\n    | IN GROUP role_name [, ...]\n    | ROLE role_name [, ...]\n    | ADMIN role_name [, ...]\n    | USER role_name [, ...]\n    | SYSID uid\n"
    },
    "CREATE RULE": {
        "description": "Description\nCREATE RULE defines a new rule applying to a specified",
        "synopsis": "\nCREATE [ OR REPLACE ] RULE name AS ON event\n    TO table_name [ WHERE condition ]\n    DO [ ALSO | INSTEAD ] { NOTHING | command | ( command ; command ... ) }\n\nwhere event can be one of:\n\n    SELECT | INSERT | UPDATE | DELETE\n"
    },
    "CREATE SCHEMA": {
        "description": "Description\nCREATE SCHEMA enters a new schema",
        "synopsis": "\nCREATE SCHEMA schema_name [ AUTHORIZATION role_specification ] [ schema_element [ ... ] ]\nCREATE SCHEMA AUTHORIZATION role_specification [ schema_element [ ... ] ]\nCREATE SCHEMA IF NOT EXISTS schema_name [ AUTHORIZATION role_specification ]\nCREATE SCHEMA IF NOT EXISTS AUTHORIZATION role_specification\nwhere role_specification can be:\n\n    [ GROUP ] user_name\n  | CURRENT_USER\n  | SESSION_USER\n"
    },
    "CREATE SEQUENCE": {
        "description": "Description\nCREATE SEQUENCE creates a new sequence number",
        "synopsis": "\nCREATE [ TEMPORARY | TEMP ] SEQUENCE [ IF NOT EXISTS ] name [ INCREMENT [ BY ] increment ]\n    [ MINVALUE minvalue | NO MINVALUE ] [ MAXVALUE maxvalue | NO MAXVALUE ]\n    [ START [ WITH ] start ] [ CACHE cache ] [ [ NO ] CYCLE ]\n    [ OWNED BY { table_name.column_name | NONE } ]\n"
    },
    "CREATE SERVER": {
        "description": "Description\nCREATE SERVER defines a new foreign server.  The",
        "synopsis": "\nCREATE SERVER server_name [ TYPE 'server_type' ] [ VERSION 'server_version' ]\n    FOREIGN DATA WRAPPER fdw_name\n    [ OPTIONS ( option 'value' [, ... ] ) ]\n"
    },
    "CREATE TABLE": {
        "description": "Description\nCREATE TABLE will create a new, initially empty table",
        "synopsis": "\nCREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name ( [\n  { column_name data_type [ COLLATE collation ] [ column_constraint [ ... ] ]\n    | table_constraint\n    | LIKE source_table [ like_option ... ] }\n    [, ... ]\n] )\n[ INHERITS ( parent_table [, ... ] ) ]\n[ WITH ( storage_parameter [= value] [, ... ] ) | WITH OIDS | WITHOUT OIDS ]\n[ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]\n[ TABLESPACE tablespace_name ]\n\nCREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name\n    OF type_name [ (\n  { column_name WITH OPTIONS [ column_constraint [ ... ] ]\n    | table_constraint }\n    [, ... ]\n) ]\n[ WITH ( storage_parameter [= value] [, ... ] ) | WITH OIDS | WITHOUT OIDS ]\n[ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]\n[ TABLESPACE tablespace_name ]\n\nwhere column_constraint is:\n\n[ CONSTRAINT constraint_name ]\n{ NOT NULL |\n  NULL |\n  CHECK ( expression ) [ NO INHERIT ] |\n  DEFAULT default_expr |\n  UNIQUE index_parameters |\n  PRIMARY KEY index_parameters |\n  REFERENCES reftable [ ( refcolumn ) ] [ MATCH FULL | MATCH PARTIAL | MATCH SIMPLE ]\n    [ ON DELETE action ] [ ON UPDATE action ] }\n[ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]\n\nand table_constraint is:\n\n[ CONSTRAINT constraint_name ]\n{ CHECK ( expression ) [ NO INHERIT ] |\n  UNIQUE ( column_name [, ... ] ) index_parameters |\n  PRIMARY KEY ( column_name [, ... ] ) index_parameters |\n  EXCLUDE [ USING index_method ] ( exclude_element WITH operator [, ... ] ) index_parameters [ WHERE ( predicate ) ] |\n  FOREIGN KEY ( column_name [, ... ] ) REFERENCES reftable [ ( refcolumn [, ... ] ) ]\n    [ MATCH FULL | MATCH PARTIAL | MATCH SIMPLE ] [ ON DELETE action ] [ ON UPDATE action ] }\n[ DEFERRABLE | NOT DEFERRABLE ] [ INITIALLY DEFERRED | INITIALLY IMMEDIATE ]\n\nand like_option is:\n\n{ INCLUDING | EXCLUDING } { DEFAULTS | CONSTRAINTS | INDEXES | STORAGE | COMMENTS | ALL }\n\nindex_parameters in UNIQUE, PRIMARY KEY, and EXCLUDE constraints are:\n\n[ WITH ( storage_parameter [= value] [, ... ] ) ]\n[ USING INDEX TABLESPACE tablespace_name ]\n\nexclude_element in an EXCLUDE constraint is:\n\n{ column_name | ( expression ) } [ opclass ] [ ASC | DESC ] [ NULLS { FIRST | LAST } ]\n"
    },
    "CREATE TABLE AS": {
        "description": "Description\nCREATE TABLE AS creates a table and fills it",
        "synopsis": "\nCREATE [ [ GLOBAL | LOCAL ] { TEMPORARY | TEMP } | UNLOGGED ] TABLE [ IF NOT EXISTS ] table_name\n    [ (column_name [, ...] ) ]\n    [ WITH ( storage_parameter [= value] [, ... ] ) | WITH OIDS | WITHOUT OIDS ]\n    [ ON COMMIT { PRESERVE ROWS | DELETE ROWS | DROP } ]\n    [ TABLESPACE tablespace_name ]\n    AS query\n    [ WITH [ NO ] DATA ]\n"
    },
    "CREATE TABLESPACE": {
        "description": "Description\nCREATE TABLESPACE registers a new cluster-wide",
        "synopsis": "\nCREATE TABLESPACE tablespace_name\n    [ OWNER { new_owner | CURRENT_USER | SESSION_USER } ]\n    LOCATION 'directory'\n    [ WITH ( tablespace_option = value [, ... ] ) ]\n"
    },
    "CREATE TRANSFORM": {
        "description": "Description\nCREATE TRANSFORM defines a new transform.",
        "synopsis": "\nCREATE [ OR REPLACE ] TRANSFORM FOR type_name LANGUAGE lang_name (\n    FROM SQL WITH FUNCTION from_sql_function_name (argument_type [, ...]),\n    TO SQL WITH FUNCTION to_sql_function_name (argument_type [, ...])\n);\n"
    },
    "CREATE TRIGGER": {
        "description": "Description\nCREATE TRIGGER creates a new trigger.  The",
        "synopsis": "\nCREATE [ CONSTRAINT ] TRIGGER name { BEFORE | AFTER | INSTEAD OF } { event [ OR ... ] }\n    ON table_name\n    [ FROM referenced_table_name ]\n    [ NOT DEFERRABLE | [ DEFERRABLE ] [ INITIALLY IMMEDIATE | INITIALLY DEFERRED ] ]\n    [ FOR [ EACH ] { ROW | STATEMENT } ]\n    [ WHEN ( condition ) ]\n    EXECUTE PROCEDURE function_name ( arguments )\n\nwhere event can be one of:\n\n    INSERT\n    UPDATE [ OF column_name [, ... ] ]\n    DELETE\n    TRUNCATE\n"
    },
    "CREATE TSCONFIG": {
        "description": "Description\nCREATE TEXT SEARCH CONFIGURATION creates a new text",
        "synopsis": "\nCREATE TEXT SEARCH CONFIGURATION name (\n    PARSER = parser_name |\n    COPY = source_config\n)\n"
    },
    "CREATE TSDICTIONARY": {
        "description": "Description\nCREATE TEXT SEARCH DICTIONARY creates a new text search",
        "synopsis": "\nCREATE TEXT SEARCH DICTIONARY name (\n    TEMPLATE = template\n    [, option = value [, ... ]]\n)\n"
    },
    "CREATE TSPARSER": {
        "description": "Description\nCREATE TEXT SEARCH PARSER creates a new text search",
        "synopsis": "\nCREATE TEXT SEARCH PARSER name (\n    START = start_function ,\n    GETTOKEN = gettoken_function ,\n    END = end_function ,\n    LEXTYPES = lextypes_function\n    [, HEADLINE = headline_function ]\n)\n"
    },
    "CREATE TSTEMPLATE": {
        "description": "Description\nCREATE TEXT SEARCH TEMPLATE creates a new text search",
        "synopsis": "\nCREATE TEXT SEARCH TEMPLATE name (\n    [ INIT = init_function , ]\n    LEXIZE = lexize_function\n)\n"
    },
    "CREATE TYPE": {
        "description": "Description\nCREATE TYPE registers a new data type for use in",
        "synopsis": "\nCREATE TYPE name AS\n    ( [ attribute_name data_type [ COLLATE collation ] [, ... ] ] )\n\nCREATE TYPE name AS ENUM\n    ( [ 'label' [, ... ] ] )\n\nCREATE TYPE name AS RANGE (\n    SUBTYPE = subtype\n    [ , SUBTYPE_OPCLASS = subtype_operator_class ]\n    [ , COLLATION = collation ]\n    [ , CANONICAL = canonical_function ]\n    [ , SUBTYPE_DIFF = subtype_diff_function ]\n)\n\nCREATE TYPE name (\n    INPUT = input_function,\n    OUTPUT = output_function\n    [ , RECEIVE = receive_function ]\n    [ , SEND = send_function ]\n    [ , TYPMOD_IN = type_modifier_input_function ]\n    [ , TYPMOD_OUT = type_modifier_output_function ]\n    [ , ANALYZE = analyze_function ]\n    [ , INTERNALLENGTH = { internallength | VARIABLE } ]\n    [ , PASSEDBYVALUE ]\n    [ , ALIGNMENT = alignment ]\n    [ , STORAGE = storage ]\n    [ , LIKE = like_type ]\n    [ , CATEGORY = category ]\n    [ , PREFERRED = preferred ]\n    [ , DEFAULT = default ]\n    [ , ELEMENT = element ]\n    [ , DELIMITER = delimiter ]\n    [ , COLLATABLE = collatable ]\n)\n\nCREATE TYPE name\n"
    },
    "CREATE USER": {
        "description": "Description\nCREATE USER is now an alias for",
        "synopsis": "\nCREATE USER name [ [ WITH ] option [ ... ] ]\n\nwhere option can be:\n\n      SUPERUSER | NOSUPERUSER\n    | CREATEDB | NOCREATEDB\n    | CREATEROLE | NOCREATEROLE\n    | CREATEUSER | NOCREATEUSER\n    | INHERIT | NOINHERIT\n    | LOGIN | NOLOGIN\n    | REPLICATION | NOREPLICATION\n    | CONNECTION LIMIT connlimit\n    | [ ENCRYPTED | UNENCRYPTED ] PASSWORD 'password'\n    | VALID UNTIL 'timestamp'\n    | IN ROLE role_name [, ...]\n    | IN GROUP role_name [, ...]\n    | ROLE role_name [, ...]\n    | ADMIN role_name [, ...]\n    | USER role_name [, ...]\n    | SYSID uid\n"
    },
    "CREATE USER MAPPING": {
        "description": "Description\nCREATE USER MAPPING defines a mapping of a user",
        "synopsis": "\nCREATE USER MAPPING FOR { user_name | USER | CURRENT_USER | PUBLIC }\n    SERVER server_name\n    [ OPTIONS ( option 'value' [ , ... ] ) ]\n"
    },
    "CREATE VIEW": {
        "description": "Description\nCREATE VIEW defines a view of a query.  The view",
        "synopsis": "\nCREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW name [ ( column_name [, ...] ) ]\n    [ WITH ( view_option_name [= view_option_value] [, ... ] ) ]\n    AS query\n    [ WITH [ CASCADED | LOCAL ] CHECK OPTION ]\n"
    },
    "CREATEDB": {
        "description": None,
        "synopsis": None
    },
    "CREATELANG": {
        "description": "Description\ncreatelang is a utility for adding a",
        "synopsis": None
    },
    "CREATEUSER": {
        "description": "Description\ncreateuser creates a",
        "synopsis": None
    },
    "DEALLOCATE": {
        "description": "Description\nDEALLOCATE is used to deallocate a previously",
        "synopsis": "\nDEALLOCATE [ PREPARE ] { name | ALL }\n"
    },
    "DECLARE": {
        "description": "Description\nDECLARE allows a user to create cursors, which",
        "synopsis": "\nDECLARE name [ BINARY ] [ INSENSITIVE ] [ [ NO ] SCROLL ]\n    CURSOR [ { WITH | WITHOUT } HOLD ] FOR query\n"
    },
    "DELETE": {
        "description": "Description\nDELETE deletes rows that satisfy the",
        "synopsis": "\n[ WITH [ RECURSIVE ] with_query [, ...] ]\nDELETE FROM [ ONLY ] table_name [ * ] [ [ AS ] alias ]\n    [ USING using_list ]\n    [ WHERE condition | WHERE CURRENT OF cursor_name ]\n    [ RETURNING * | output_expression [ [ AS ] output_name ] [, ...] ]\n"
    },
    "DISCARD": {
        "description": "Description\nDISCARD releases internal resources associated with a",
        "synopsis": "\nDISCARD { ALL | PLANS | SEQUENCES | TEMPORARY | TEMP }\n"
    },
    "DO": {
        "description": "Description\nDO executes an anonymous code block, or in other",
        "synopsis": "\nDO [ LANGUAGE lang_name ] code\n"
    },
    "DROP AGGREGATE": {
        "description": "Description\nDROP AGGREGATE removes an existing",
        "synopsis": "\nDROP AGGREGATE [ IF EXISTS ] name ( aggregate_signature ) [ CASCADE | RESTRICT ]\n\nwhere aggregate_signature is:\n\n* |\n[ argmode ] [ argname ] argtype [ , ... ] |\n[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]\n"
    },
    "DROP CAST": {
        "description": "Description\nDROP CAST removes a previously defined cast.",
        "synopsis": "\nDROP CAST [ IF EXISTS ] (source_type AS target_type) [ CASCADE | RESTRICT ]\n"
    },
    "DROP COLLATION": {
        "description": "Description\nDROP COLLATION removes a previously defined collation.",
        "synopsis": "\nDROP COLLATION [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP CONVERSION": {
        "description": "Description\nDROP CONVERSION removes a previously defined conversion.",
        "synopsis": "\nDROP CONVERSION [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP DATABASE": {
        "description": "Description\nDROP DATABASE drops a database. It removes the",
        "synopsis": "\nDROP DATABASE [ IF EXISTS ] name\n"
    },
    "DROP DOMAIN": {
        "description": "Description\nDROP DOMAIN removes a domain.  Only the owner of",
        "synopsis": "\nDROP DOMAIN [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP EVENT TRIGGER": {
        "description": "Description\nDROP EVENT TRIGGER removes an existing event trigger.",
        "synopsis": "\nDROP EVENT TRIGGER [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP EXTENSION": {
        "description": "Description\nDROP EXTENSION removes extensions from the database.",
        "synopsis": "\nDROP EXTENSION [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP FOREIGN DATA WRAPPER": {
        "description": "Description\nDROP FOREIGN DATA WRAPPER removes an existing",
        "synopsis": "\nDROP FOREIGN DATA WRAPPER [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP FOREIGN TABLE": {
        "description": "Description\nDROP FOREIGN TABLE removes a foreign table.",
        "synopsis": "\nDROP FOREIGN TABLE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP FUNCTION": {
        "description": "Description\nDROP FUNCTION removes the definition of an existing",
        "synopsis": "\nDROP FUNCTION [ IF EXISTS ] name ( [ [ argmode ] [ argname ] argtype [, ...] ] )\n    [ CASCADE | RESTRICT ]\n"
    },
    "DROP GROUP": {
        "description": "Description\nDROP GROUP is now an alias for",
        "synopsis": "\nDROP GROUP [ IF EXISTS ] name [, ...]\n"
    },
    "DROP INDEX": {
        "description": "Description\nDROP INDEX drops an existing index from the database",
        "synopsis": "\nDROP INDEX [ CONCURRENTLY ] [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP LANGUAGE": {
        "description": "Description\nDROP LANGUAGE removes the definition of a",
        "synopsis": "\nDROP [ PROCEDURAL ] LANGUAGE [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP MATERIALIZED VIEW": {
        "description": "Description\nDROP MATERIALIZED VIEW drops an existing materialized",
        "synopsis": "\nDROP MATERIALIZED VIEW [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP OPCLASS": {
        "description": "Description\nDROP OPERATOR CLASS drops an existing operator class.",
        "synopsis": "\nDROP OPERATOR CLASS [ IF EXISTS ] name USING index_method [ CASCADE | RESTRICT ]\n"
    },
    "DROP OPERATOR": {
        "description": "Description\nDROP OPERATOR drops an existing operator from",
        "synopsis": "\nDROP OPERATOR [ IF EXISTS ] name ( { left_type | NONE } , { right_type | NONE } ) [ CASCADE | RESTRICT ]\n"
    },
    "DROP OPFAMILY": {
        "description": "Description\nDROP OPERATOR FAMILY drops an existing operator family.",
        "synopsis": "\nDROP OPERATOR FAMILY [ IF EXISTS ] name USING index_method [ CASCADE | RESTRICT ]\n"
    },
    "DROP OWNED": {
        "description": "Description\nDROP OWNED drops all the objects within the current",
        "synopsis": "\nDROP OWNED BY { name | CURRENT_USER | SESSION_USER } [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP POLICY": {
        "description": "Description\nDROP POLICY removes the specified policy from the table.",
        "synopsis": "\nDROP POLICY [ IF EXISTS ] name ON table_name\n"
    },
    "DROP ROLE": {
        "description": "Description\nDROP ROLE removes the specified role(s).",
        "synopsis": "\nDROP ROLE [ IF EXISTS ] name [, ...]\n"
    },
    "DROP RULE": {
        "description": "Description\nDROP RULE drops a rewrite rule.",
        "synopsis": "\nDROP RULE [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]\n"
    },
    "DROP SCHEMA": {
        "description": "Description\nDROP SCHEMA removes schemas from the database.",
        "synopsis": "\nDROP SCHEMA [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP SEQUENCE": {
        "description": "Description\nDROP SEQUENCE removes sequence number",
        "synopsis": "\nDROP SEQUENCE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP SERVER": {
        "description": "Description\nDROP SERVER removes an existing foreign server",
        "synopsis": "\nDROP SERVER [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP TABLE": {
        "description": "Description\nDROP TABLE removes tables from the database.",
        "synopsis": "\nDROP TABLE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP TABLESPACE": {
        "description": "Description\nDROP TABLESPACE removes a tablespace from the system.",
        "synopsis": "\nDROP TABLESPACE [ IF EXISTS ] name\n"
    },
    "DROP TRANSFORM": {
        "description": "Description\nDROP TRANSFORM removes a previously defined transform.",
        "synopsis": "\nDROP TRANSFORM [ IF EXISTS ] FOR type_name LANGUAGE lang_name\n"
    },
    "DROP TRIGGER": {
        "description": "Description\nDROP TRIGGER removes an existing",
        "synopsis": "\nDROP TRIGGER [ IF EXISTS ] name ON table_name [ CASCADE | RESTRICT ]\n"
    },
    "DROP TSCONFIG": {
        "description": "Description\nDROP TEXT SEARCH CONFIGURATION drops an existing text",
        "synopsis": "\nDROP TEXT SEARCH CONFIGURATION [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP TSDICTIONARY": {
        "description": "Description\nDROP TEXT SEARCH DICTIONARY drops an existing text",
        "synopsis": "\nDROP TEXT SEARCH DICTIONARY [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP TSPARSER": {
        "description": "Description\nDROP TEXT SEARCH PARSER drops an existing text search",
        "synopsis": "\nDROP TEXT SEARCH PARSER [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP TSTEMPLATE": {
        "description": "Description\nDROP TEXT SEARCH TEMPLATE drops an existing text search",
        "synopsis": "\nDROP TEXT SEARCH TEMPLATE [ IF EXISTS ] name [ CASCADE | RESTRICT ]\n"
    },
    "DROP TYPE": {
        "description": "Description\nDROP TYPE removes a user-defined data type.",
        "synopsis": "\nDROP TYPE [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROP USER": {
        "description": "Description\nDROP USER is now an alias for",
        "synopsis": "\nDROP USER [ IF EXISTS ] name [, ...]\n"
    },
    "DROP USER MAPPING": {
        "description": "Description\nDROP USER MAPPING removes an existing user",
        "synopsis": "\nDROP USER MAPPING [ IF EXISTS ] FOR { user_name | USER | CURRENT_USER | PUBLIC } SERVER server_name\n"
    },
    "DROP VIEW": {
        "description": "Description\nDROP VIEW drops an existing view.  To execute",
        "synopsis": "\nDROP VIEW [ IF EXISTS ] name [, ...] [ CASCADE | RESTRICT ]\n"
    },
    "DROPDB": {
        "description": "Description\ndropdb destroys an existing",
        "synopsis": None
    },
    "DROPLANG": {
        "description": None,
        "synopsis": None
    },
    "DROPUSER": {
        "description": "Description\ndropuser removes an existing",
        "synopsis": None
    },
    "ECPG-REF": {
        "description": "Description\necpg is the embedded SQL preprocessor for C",
        "synopsis": None
    },
    "END": {
        "description": "Description\nEND commits the current transaction. All changes",
        "synopsis": "\nEND [ WORK | TRANSACTION ]\n"
    },
    "EXECUTE": {
        "description": "Description\nEXECUTE is used to execute a previously prepared",
        "synopsis": "\nEXECUTE name [ ( parameter [, ...] ) ]\n"
    },
    "EXPLAIN": {
        "description": "Description\n   This command displays the execution plan that the",
        "synopsis": "\nEXPLAIN [ ( option [, ...] ) ] statement\nEXPLAIN [ ANALYZE ] [ VERBOSE ] statement\nwhere option can be one of:\n\n    ANALYZE [ boolean ]\n    VERBOSE [ boolean ]\n    COSTS [ boolean ]\n    BUFFERS [ boolean ]\n    TIMING [ boolean ]\n    FORMAT { TEXT | XML | JSON | YAML }\n"
    },
    "FETCH": {
        "description": "Description\nFETCH retrieves rows using a previously-created cursor.",
        "synopsis": "\nFETCH [ direction [ FROM | IN ] ] cursor_name\nwhere direction can be empty or one of:\n\n    NEXT\n    PRIOR\n    FIRST\n    LAST\n    ABSOLUTE count\n    RELATIVE count\ncount\n    ALL\n    FORWARD\n    FORWARD count\n    FORWARD ALL\n    BACKWARD\n    BACKWARD count\n    BACKWARD ALL\n"
    },
    "GRANT": {
        "description": "Description\n   The GRANT command has two basic variants: one",
        "synopsis": "\nGRANT { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON { [ TABLE ] table_name [, ...]\n         | ALL TABLES IN SCHEMA schema_name [, ...] }\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { { SELECT | INSERT | UPDATE | REFERENCES } ( column_name [, ...] )\n    [, ...] | ALL [ PRIVILEGES ] ( column_name [, ...] ) }\n    ON [ TABLE ] table_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { { USAGE | SELECT | UPDATE }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON { SEQUENCE sequence_name [, ...]\n         | ALL SEQUENCES IN SCHEMA schema_name [, ...] }\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { { CREATE | CONNECT | TEMPORARY | TEMP } [, ...] | ALL [ PRIVILEGES ] }\n    ON DATABASE database_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { USAGE | ALL [ PRIVILEGES ] }\n    ON DOMAIN domain_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { USAGE | ALL [ PRIVILEGES ] }\n    ON FOREIGN DATA WRAPPER fdw_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { USAGE | ALL [ PRIVILEGES ] }\n    ON FOREIGN SERVER server_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { EXECUTE | ALL [ PRIVILEGES ] }\n    ON { FUNCTION function_name ( [ [ argmode ] [ arg_name ] arg_type [, ...] ] ) [, ...]\n         | ALL FUNCTIONS IN SCHEMA schema_name [, ...] }\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { USAGE | ALL [ PRIVILEGES ] }\n    ON LANGUAGE lang_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { { SELECT | UPDATE } [, ...] | ALL [ PRIVILEGES ] }\n    ON LARGE OBJECT loid [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { { CREATE | USAGE } [, ...] | ALL [ PRIVILEGES ] }\n    ON SCHEMA schema_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { CREATE | ALL [ PRIVILEGES ] }\n    ON TABLESPACE tablespace_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nGRANT { USAGE | ALL [ PRIVILEGES ] }\n    ON TYPE type_name [, ...]\n    TO role_specification [, ...] [ WITH GRANT OPTION ]\n\nwhere role_specification can be:\n\n    [ GROUP ] role_name\n  | PUBLIC\n  | CURRENT_USER\n  | SESSION_USER\n\nGRANT role_name [, ...] TO role_name [, ...] [ WITH ADMIN OPTION ]\n"
    },
    "IMPORT FOREIGN SCHEMA": {
        "description": "Description\nIMPORT FOREIGN SCHEMA creates foreign tables that",
        "synopsis": "\nIMPORT FOREIGN SCHEMA remote_schema\n    [ { LIMIT TO | EXCEPT } ( table_name [, ...] ) ]\n    FROM SERVER server_name\n    INTO local_schema\n    [ OPTIONS ( option 'value' [, ... ] ) ]\n"
    },
    "INITDB": {
        "description": None,
        "synopsis": None
    },
    "INSERT": {
        "description": "Description\nINSERT inserts new rows into a table.",
        "synopsis": "\n[ WITH [ RECURSIVE ] with_query [, ...] ]\nINSERT INTO table_name [ AS alias ] [ ( column_name [, ...] ) ]\n    { DEFAULT VALUES | VALUES ( { expression | DEFAULT } [, ...] ) [, ...] | query }\n    [ ON CONFLICT [ conflict_target ] conflict_action ]\n    [ RETURNING * | output_expression [ [ AS ] output_name ] [, ...] ]\n\nwhere conflict_target can be one of:\n\n    ( { column_name_index | ( expression_index ) } [ COLLATE collation ] [ opclass ] [, ...] ) [ WHERE index_predicate ]\n    ON CONSTRAINT constraint_name\nand conflict_action is one of:\n\n    DO NOTHING\n    DO UPDATE SET { column_name = { expression | DEFAULT } |\n                    ( column_name [, ...] ) = ( { expression | DEFAULT } [, ...] ) |\n                    ( column_name [, ...] ) = ( sub-SELECT )\n                  } [, ...]\n              [ WHERE condition ]\n"
    },
    "LISTEN": {
        "description": "Description\nLISTEN registers the current session as a",
        "synopsis": "\nLISTEN channel\n"
    },
    "LOAD": {
        "description": "Description\n   This command loads a shared library file into the PostgreSQL",
        "synopsis": "\nLOAD 'filename'\n"
    },
    "LOCK": {
        "description": "Description\nLOCK TABLE obtains a table-level lock, waiting",
        "synopsis": "\nLOCK [ TABLE ] [ ONLY ] name [ * ] [, ...] [ IN lockmode MODE ] [ NOWAIT ]\n\nwhere lockmode is one of:\n\n    ACCESS SHARE | ROW SHARE | ROW EXCLUSIVE | SHARE UPDATE EXCLUSIVE\n    | SHARE | SHARE ROW EXCLUSIVE | EXCLUSIVE | ACCESS EXCLUSIVE\n"
    },
    "MOVE": {
        "description": "Description\nMOVE repositions a cursor without retrieving any data.",
        "synopsis": "\nMOVE [ direction [ FROM | IN ] ] cursor_name\nwhere direction can be empty or one of:\n\n    NEXT\n    PRIOR\n    FIRST\n    LAST\n    ABSOLUTE count\n    RELATIVE count\ncount\n    ALL\n    FORWARD\n    FORWARD count\n    FORWARD ALL\n    BACKWARD\n    BACKWARD count\n    BACKWARD ALL\n"
    },
    "NOTIFY": {
        "description": "Description\n   The NOTIFY command sends a notification event together",
        "synopsis": "\nNOTIFY channel [ , payload ]\n"
    },
    "PG BASEBACKUP": {
        "description": None,
        "synopsis": None
    },
    "PG CONFIG-REF": {
        "description": "Description\n   The pg_config utility prints configuration parameters",
        "synopsis": None
    },
    "PG CONTROLDATA": {
        "description": "Description\npg_controldata prints information initialized during",
        "synopsis": None
    },
    "PG CTL-REF": {
        "description": "Description\npg_ctl is a utility for initializing a",
        "synopsis": None
    },
    "PG DUMP": {
        "description": None,
        "synopsis": None
    },
    "PG DUMPALL": {
        "description": "Description\npg_dumpall is a utility for writing out",
        "synopsis": None
    },
    "PG ISREADY": {
        "description": "Description\npg_isready is a utility for checking the connection",
        "synopsis": None
    },
    "PG RECEIVEXLOG": {
        "description": None,
        "synopsis": None
    },
    "PG RECVLOGICAL": {
        "description": "Description\npg_recvlogical controls logical decoding replication",
        "synopsis": None
    },
    "PG RESETXLOG": {
        "description": "Description\npg_resetxlog clears the write-ahead log (WAL) and",
        "synopsis": None
    },
    "PG RESTORE": {
        "description": "Description\npg_restore is a utility for restoring a",
        "synopsis": None
    },
    "PG REWIND": {
        "description": "Description\npg_rewind is a tool for synchronizing a PostgreSQL cluster",
        "synopsis": None
    },
    "PG XLOGDUMP": {
        "description": "Description\npg_xlogdump displays the write-ahead log (WAL) and is mainly",
        "synopsis": None
    },
    "PGARCHIVECLEANUP": {
        "description": "Description\npg_archivecleanup is designed to be used as an",
        "synopsis": None
    },
    "PGBENCH": {
        "description": "Description\npgbench is a simple program for running benchmark",
        "synopsis": "\nclient_id transaction_no time file_no time_epoch time_us schedule_lag\n"
    },
    "PGTESTFSYNC": {
        "description": "Description\npg_test_fsync is intended to give you a reasonable",
        "synopsis": None
    },
    "PGTESTTIMING": {
        "description": "Description\npg_test_timing is a tool to measure the timing overhead",
        "synopsis": None
    },
    "PGUPGRADE": {
        "description": "Description\npg_upgrade (formerly called pg_migrator) allows data",
        "synopsis": None
    },
    "POSTGRES-REF": {
        "description": "Description\npostgres is the",
        "synopsis": None
    },
    "POSTMASTER": {
        "description": "Description\npostmaster is a deprecated alias of postgres.",
        "synopsis": None
    },
    "PREPARE": {
        "description": "Description\nPREPARE creates a prepared statement. A prepared",
        "synopsis": "\nPREPARE name [ ( data_type [, ...] ) ] AS statement\n"
    },
    "PREPARE TRANSACTION": {
        "description": "Description\nPREPARE TRANSACTION prepares the current transaction",
        "synopsis": "\nPREPARE TRANSACTION transaction_id\n"
    },
    "PSQL-REF": {
        "description": "Description\npsql is a terminal-based front-end to",
        "synopsis": None
    },
    "REASSIGN OWNED": {
        "description": "Description\nREASSIGN OWNED instructs the system to change",
        "synopsis": "\nREASSIGN OWNED BY { old_role | CURRENT_USER | SESSION_USER } [, ...]\n               TO { new_role | CURRENT_USER | SESSION_USER }\n"
    },
    "REFRESH MATERIALIZED VIEW": {
        "description": "Description\nREFRESH MATERIALIZED VIEW completely replaces the",
        "synopsis": "\nREFRESH MATERIALIZED VIEW [ CONCURRENTLY ] name\n    [ WITH [ NO ] DATA ]\n"
    },
    "REINDEX": {
        "description": "Description\nREINDEX rebuilds an index using the data",
        "synopsis": "\nREINDEX [ ( { VERBOSE } [, ...] ) ] { INDEX | TABLE | SCHEMA | DATABASE | SYSTEM } name\n"
    },
    "REINDEXDB": {
        "description": "Description\nreindexdb is a utility for rebuilding indexes",
        "synopsis": None
    },
    "RELEASE SAVEPOINT": {
        "description": "Description\nRELEASE SAVEPOINT destroys a savepoint previously defined",
        "synopsis": "\nRELEASE [ SAVEPOINT ] savepoint_name\n"
    },
    "RESET": {
        "description": "Description\nRESET restores run-time parameters to their",
        "synopsis": "\nRESET configuration_parameter\nRESET ALL\n"
    },
    "REVOKE": {
        "description": "Description\n   The REVOKE command revokes previously granted",
        "synopsis": "\nREVOKE [ GRANT OPTION FOR ]\n    { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON { [ TABLE ] table_name [, ...]\n         | ALL TABLES IN SCHEMA schema_name [, ...] }\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { SELECT | INSERT | UPDATE | REFERENCES } ( column_name [, ...] )\n    [, ...] | ALL [ PRIVILEGES ] ( column_name [, ...] ) }\n    ON [ TABLE ] table_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { USAGE | SELECT | UPDATE }\n    [, ...] | ALL [ PRIVILEGES ] }\n    ON { SEQUENCE sequence_name [, ...]\n         | ALL SEQUENCES IN SCHEMA schema_name [, ...] }\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { CREATE | CONNECT | TEMPORARY | TEMP } [, ...] | ALL [ PRIVILEGES ] }\n    ON DATABASE database_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON DOMAIN domain_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON FOREIGN DATA WRAPPER fdw_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON FOREIGN SERVER server_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { EXECUTE | ALL [ PRIVILEGES ] }\n    ON { FUNCTION function_name ( [ [ argmode ] [ arg_name ] arg_type [, ...] ] ) [, ...]\n         | ALL FUNCTIONS IN SCHEMA schema_name [, ...] }\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON LANGUAGE lang_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { SELECT | UPDATE } [, ...] | ALL [ PRIVILEGES ] }\n    ON LARGE OBJECT loid [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { { CREATE | USAGE } [, ...] | ALL [ PRIVILEGES ] }\n    ON SCHEMA schema_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { CREATE | ALL [ PRIVILEGES ] }\n    ON TABLESPACE tablespace_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ GRANT OPTION FOR ]\n    { USAGE | ALL [ PRIVILEGES ] }\n    ON TYPE type_name [, ...]\n    FROM { [ GROUP ] role_name | PUBLIC } [, ...]\n    [ CASCADE | RESTRICT ]\n\nREVOKE [ ADMIN OPTION FOR ]\n    role_name [, ...] FROM role_name [, ...]\n    [ CASCADE | RESTRICT ]\n"
    },
    "ROLLBACK": {
        "description": "Description\nROLLBACK rolls back the current transaction and causes",
        "synopsis": "\nROLLBACK [ WORK | TRANSACTION ]\n"
    },
    "ROLLBACK PREPARED": {
        "description": "Description\nROLLBACK PREPARED rolls back a transaction that is in",
        "synopsis": "\nROLLBACK PREPARED transaction_id\n"
    },
    "ROLLBACK TO": {
        "description": "Description\n   Roll back all commands that were executed after the savepoint was",
        "synopsis": "\nROLLBACK [ WORK | TRANSACTION ] TO [ SAVEPOINT ] savepoint_name\n"
    },
    "SAVEPOINT": {
        "description": "Description\nSAVEPOINT establishes a new savepoint within",
        "synopsis": "\nSAVEPOINT savepoint_name\n"
    },
    "SECURITY LABEL": {
        "description": "Description\nSECURITY LABEL applies a security label to a database",
        "synopsis": "\nSECURITY LABEL [ FOR provider ] ON\n{\n  TABLE object_name |\n  COLUMN table_name.column_name |\n  AGGREGATE aggregate_name ( aggregate_signature ) |\n  DATABASE object_name |\n  DOMAIN object_name |\n  EVENT TRIGGER object_name |\n  FOREIGN TABLE object_name\n  FUNCTION function_name ( [ [ argmode ] [ argname ] argtype [, ...] ] ) |\n  LARGE OBJECT large_object_oid |\n  MATERIALIZED VIEW object_name |\n  [ PROCEDURAL ] LANGUAGE object_name |\n  ROLE object_name |\n  SCHEMA object_name |\n  SEQUENCE object_name |\n  TABLESPACE object_name |\n  TYPE object_name |\n  VIEW object_name\n} IS 'label'\n\nwhere aggregate_signature is:\n\n* |\n[ argmode ] [ argname ] argtype [ , ... ] |\n[ [ argmode ] [ argname ] argtype [ , ... ] ] ORDER BY [ argmode ] [ argname ] argtype [ , ... ]\n"
    },
    "SELECT": {
        "description": "Description\nSELECT retrieves rows from zero or more tables.",
        "synopsis": "\n[ WITH [ RECURSIVE ] with_query [, ...] ]\nSELECT [ ALL | DISTINCT [ ON ( expression [, ...] ) ] ]\n    [ * | expression [ [ AS ] output_name ] [, ...] ]\n    [ FROM from_item [, ...] ]\n    [ WHERE condition ]\n    [ GROUP BY grouping_element [, ...] ]\n    [ HAVING condition [, ...] ]\n    [ WINDOW window_name AS ( window_definition ) [, ...] ]\n    [ { UNION | INTERSECT | EXCEPT } [ ALL | DISTINCT ] select ]\n    [ ORDER BY expression [ ASC | DESC | USING operator ] [ NULLS { FIRST | LAST } ] [, ...] ]\n    [ LIMIT { count | ALL } ]\n    [ OFFSET start [ ROW | ROWS ] ]\n    [ FETCH { FIRST | NEXT } [ count ] { ROW | ROWS } ONLY ]\n    [ FOR { UPDATE | NO KEY UPDATE | SHARE | KEY SHARE } [ OF table_name [, ...] ] [ NOWAIT | SKIP LOCKED ] [...] ]\n\nwhere from_item can be one of:\n\n    [ ONLY ] table_name [ * ] [ [ AS ] alias [ ( column_alias [, ...] ) ] ]\n                [ TABLESAMPLE sampling_method ( argument [, ...] ) [ REPEATABLE ( seed ) ] ]\n    [ LATERAL ] ( select ) [ AS ] alias [ ( column_alias [, ...] ) ]\n    with_query_name [ [ AS ] alias [ ( column_alias [, ...] ) ] ]\n    [ LATERAL ] function_name ( [ argument [, ...] ] )\n                [ WITH ORDINALITY ] [ [ AS ] alias [ ( column_alias [, ...] ) ] ]\n    [ LATERAL ] function_name ( [ argument [, ...] ] ) [ AS ] alias ( column_definition [, ...] )\n    [ LATERAL ] function_name ( [ argument [, ...] ] ) AS ( column_definition [, ...] )\n    [ LATERAL ] ROWS FROM( function_name ( [ argument [, ...] ] ) [ AS ( column_definition [, ...] ) ] [, ...] )\n                [ WITH ORDINALITY ] [ [ AS ] alias [ ( column_alias [, ...] ) ] ]\n    from_item [ NATURAL ] join_type from_item [ ON join_condition | USING ( join_column [, ...] ) ]\n\nand grouping_element can be one of:\n\n    ( )\n    expression\n    ( expression [, ...] )\n    ROLLUP ( { expression | ( expression [, ...] ) } [, ...] )\n    CUBE ( { expression | ( expression [, ...] ) } [, ...] )\n    GROUPING SETS ( grouping_element [, ...] )\n\nand with_query is:\nwith_query_name [ ( column_name [, ...] ) ] AS ( select | values | insert | update | delete )\n\nTABLE [ ONLY ] table_name [ * ]\n"
    },
    "SELECT INTO": {
        "description": "Description\nSELECT INTO creates a new table and fills it",
        "synopsis": "\n[ WITH [ RECURSIVE ] with_query [, ...] ]\nSELECT [ ALL | DISTINCT [ ON ( expression [, ...] ) ] ]\n    * | expression [ [ AS ] output_name ] [, ...]\n    INTO [ TEMPORARY | TEMP | UNLOGGED ] [ TABLE ] new_table\n    [ FROM from_item [, ...] ]\n    [ WHERE condition ]\n    [ GROUP BY expression [, ...] ]\n    [ HAVING condition [, ...] ]\n    [ WINDOW window_name AS ( window_definition ) [, ...] ]\n    [ { UNION | INTERSECT | EXCEPT } [ ALL | DISTINCT ] select ]\n    [ ORDER BY expression [ ASC | DESC | USING operator ] [ NULLS { FIRST | LAST } ] [, ...] ]\n    [ LIMIT { count | ALL } ]\n    [ OFFSET start [ ROW | ROWS ] ]\n    [ FETCH { FIRST | NEXT } [ count ] { ROW | ROWS } ONLY ]\n    [ FOR { UPDATE | SHARE } [ OF table_name [, ...] ] [ NOWAIT ] [...] ]\n"
    },
    "SET": {
        "description": "Description\n   The SET command changes run-time configuration",
        "synopsis": "\nSET [ SESSION | LOCAL ] configuration_parameter { TO | = } { value | 'value' | DEFAULT }\nSET [ SESSION | LOCAL ] TIME ZONE { timezone | LOCAL | DEFAULT }\n"
    },
    "SET CONSTRAINTS": {
        "description": "Description\nSET CONSTRAINTS sets the behavior of constraint",
        "synopsis": "\nSET CONSTRAINTS { ALL | name [, ...] } { DEFERRED | IMMEDIATE }\n"
    },
    "SET ROLE": {
        "description": "Description\n   This command sets the current user",
        "synopsis": "\nSET [ SESSION | LOCAL ] ROLE role_name\nSET [ SESSION | LOCAL ] ROLE NONE\nRESET ROLE\n"
    },
    "SET SESSION AUTH": {
        "description": "Description\n   This command sets the session user identifier and the current user",
        "synopsis": "\nSET [ SESSION | LOCAL ] SESSION AUTHORIZATION user_name\nSET [ SESSION | LOCAL ] SESSION AUTHORIZATION DEFAULT\nRESET SESSION AUTHORIZATION\n"
    },
    "SET TRANSACTION": {
        "description": "Description\n   The SET TRANSACTION command sets the",
        "synopsis": "\nSET TRANSACTION transaction_mode [, ...]\nSET TRANSACTION SNAPSHOT snapshot_id\nSET SESSION CHARACTERISTICS AS TRANSACTION transaction_mode [, ...]\n\nwhere transaction_mode is one of:\n\n    ISOLATION LEVEL { SERIALIZABLE | REPEATABLE READ | READ COMMITTED | READ UNCOMMITTED }\n    READ WRITE | READ ONLY\n    [ NOT ] DEFERRABLE\n"
    },
    "SHOW": {
        "description": "Description\nSHOW will display the current setting of",
        "synopsis": "\nSHOW name\nSHOW ALL\n"
    },
    "START TRANSACTION": {
        "description": "Description\n   This command begins a new transaction block. If the isolation level,",
        "synopsis": "\nSTART TRANSACTION [ transaction_mode [, ...] ]\n\nwhere transaction_mode is one of:\n\n    ISOLATION LEVEL { SERIALIZABLE | REPEATABLE READ | READ COMMITTED | READ UNCOMMITTED }\n    READ WRITE | READ ONLY\n    [ NOT ] DEFERRABLE\n"
    },
    "TRUNCATE": {
        "description": "Description\nTRUNCATE quickly removes all rows from a set of",
        "synopsis": "\nTRUNCATE [ TABLE ] [ ONLY ] name [ * ] [, ... ]\n    [ RESTART IDENTITY | CONTINUE IDENTITY ] [ CASCADE | RESTRICT ]\n"
    },
    "UNLISTEN": {
        "description": "Description\nUNLISTEN is used to remove an existing",
        "synopsis": "\nUNLISTEN { channel | * }\n"
    },
    "UPDATE": {
        "description": "Description\nUPDATE changes the values of the specified",
        "synopsis": "\n[ WITH [ RECURSIVE ] with_query [, ...] ]\nUPDATE [ ONLY ] table_name [ * ] [ [ AS ] alias ]\n    SET { column_name = { expression | DEFAULT } |\n          ( column_name [, ...] ) = ( { expression | DEFAULT } [, ...] ) |\n          ( column_name [, ...] ) = ( sub-SELECT )\n        } [, ...]\n    [ FROM from_list ]\n    [ WHERE condition | WHERE CURRENT OF cursor_name ]\n    [ RETURNING * | output_expression [ [ AS ] output_name ] [, ...] ]\n"
    },
    "VACUUM": {
        "description": "Description\nVACUUM reclaims storage occupied by dead tuples.",
        "synopsis": "\nVACUUM [ ( { FULL | FREEZE | VERBOSE | ANALYZE } [, ...] ) ] [ table_name [ (column_name [, ...] ) ] ]\nVACUUM [ FULL ] [ FREEZE ] [ VERBOSE ] [ table_name ]\nVACUUM [ FULL ] [ FREEZE ] [ VERBOSE ] ANALYZE [ table_name [ (column_name [, ...] ) ] ]\n"
    },
    "VACUUMDB": {
        "description": "Description\nvacuumdb is a utility for cleaning a",
        "synopsis": None
    },
    "VALUES": {
        "description": "Description\nVALUES computes a row value or set of row values",
        "synopsis": "\nVALUES ( expression [, ...] ) [, ...]\n    [ ORDER BY sort_expression [ ASC | DESC | USING operator ] [, ...] ]\n    [ LIMIT { count | ALL } ]\n    [ OFFSET start [ ROW | ROWS ] ]\n    [ FETCH { FIRST | NEXT } [ count ] { ROW | ROWS } ONLY ]\n"
    }
}
