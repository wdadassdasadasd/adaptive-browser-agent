-- Run through a separately authorized local PostgreSQL 16 psql connection.
-- Pass expected_db, expected_role, own_schema, other_schema and other_db as psql variables.
-- The role matrix is deliberately fixed by the later operation card, not inferred here.
\set ON_ERROR_STOP on
\set QUIET on
BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
SET LOCAL lock_timeout = '2s';

WITH checks AS (
    SELECT
        current_database() = :'expected_db' AS expected_database,
        current_user = :'expected_role' AND session_user = :'expected_role' AS expected_login,
        current_setting('server_version_num') = '160015' AS expected_postgres,
        current_setting('port') = '55432' AS expected_port,
        inet_server_addr() IS NULL AS local_unix_socket,
        current_setting('listen_addresses') = '' AS tcp_listener_disabled,
        r.rolcanlogin AND NOT (r.rolsuper OR r.rolcreatedb OR r.rolcreaterole OR r.rolreplication OR r.rolbypassrls)
            AS restricted_login,
        NOT EXISTS (
            SELECT FROM pg_catalog.pg_roles AS reachable
            WHERE reachable.oid <> r.oid
              AND pg_catalog.pg_has_role(r.oid, reachable.oid, 'MEMBER')
        ) AS no_other_role_membership,
        NOT pg_catalog.has_database_privilege(current_user, current_database(), 'CREATE') AS no_create_schema,
        NOT pg_catalog.has_database_privilege(current_user, current_database(), 'TEMP') AS no_temp_tables,
        NOT pg_catalog.has_database_privilege(current_user, :'other_db', 'CONNECT') AS no_cross_database_connect,
        pg_catalog.has_schema_privilege(current_user, :'own_schema', 'USAGE') AS own_schema_usage,
        NOT pg_catalog.has_schema_privilege(current_user, :'other_schema', 'USAGE') AS no_other_schema_usage,
        NOT EXISTS (
            SELECT FROM pg_catalog.pg_namespace AS ns
            WHERE ns.nspname NOT LIKE 'pg_temp_%'
              AND ns.nspname NOT LIKE 'pg_toast_temp_%'
              AND pg_catalog.has_schema_privilege(current_user, ns.oid, 'CREATE')
        ) AS no_schema_create,
        NOT EXISTS (
            SELECT FROM pg_catalog.pg_class AS rel WHERE rel.relowner = r.oid
        ) AND NOT EXISTS (
            SELECT FROM pg_catalog.pg_namespace AS ns WHERE ns.nspowner = r.oid
        ) AND NOT EXISTS (
            SELECT FROM pg_catalog.pg_database AS db WHERE db.datdba = r.oid
        ) AS no_runtime_ownership
    FROM pg_catalog.pg_roles AS r WHERE r.rolname = current_user
)
SELECT value AS passed, key AS check FROM checks,
    LATERAL jsonb_each_text(to_jsonb(checks)) ORDER BY key;
ROLLBACK;
