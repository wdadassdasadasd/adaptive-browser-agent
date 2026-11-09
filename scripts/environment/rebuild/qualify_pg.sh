#!/bin/bash
# Fixed, offline stage-one qualification. Secrets never leave this guest.
set -euo pipefail
umask 077
work=/tmp/ara-rebuild
data=/var/lib/postgresql/16/ara_m1
conf=/etc/postgresql/16/ara_m1
cg=/sys/fs/cgroup/ara-stage1/pg
secret=/var/lib/ara-m1/credentials
pg_started=0
guard_written=0
cluster_guard_written=0
stage=preflight
assert_interop_fenced() {
  if test -e /proc/sys/fs/binfmt_misc/WSLInterop; then
    test "$(head -n1 /proc/sys/fs/binfmt_misc/WSLInterop)" = disabled
  fi
}
assert_interop_fenced
assert_no_pg_tcp() {
  # ss is absent from the signed Ubuntu Base. Read the kernel's actual IPv4/6
  # listeners; a missing diagnostic must never be mistaken for no listeners.
  test -r /proc/net/tcp; test -r /proc/net/tcp6
  awk 'FNR>1 && $4=="0A" {split($2,a,":"); if(a[2]=="1538" || a[2]=="1539" || a[2]=="D888") found=1} END {exit(found ? 1 : 0)}' /proc/net/tcp /proc/net/tcp6
}
cleanup() {
  code=$?
  if [ "$code" != 0 ]; then
    printf 'PG_QUALIFICATION_FAILED stage=%s exit=%s\n' "$stage" "$code"
    # Provisioning/connection logs may contain secrets on an unexpected SQL error.
    # Only package/start logs are permitted in the host diagnostic channel.
    case "$stage" in install) tail -c 8192 "$work/dpkg.log" 2>/dev/null || true;; start|recovery) tail -c 8192 "$work/start.log" 2>/dev/null || true;; esac
  fi
  if [ "$pg_started" = 1 ]; then pg_ctlcluster --skip-systemctl-redirect 16 ara_m1 stop -m fast >/dev/null 2>&1 || true; fi
  [ "$guard_written" = 0 ] || rm -f /usr/sbin/policy-rc.d
  [ "$cluster_guard_written" = 0 ] || rm -f /etc/postgresql-common/createcluster.conf
  rm -f "$work/roles-private.sql" /var/lib/postgresql/ara-rebuild-roles.sql
  exit "$code"
}
trap cleanup EXIT
test ! -e /usr/sbin/policy-rc.d
test ! -e /etc/postgresql-common/createcluster.conf
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
chmod 755 /usr/sbin/policy-rc.d
guard_written=1
mkdir -p /etc/postgresql-common
printf "create_main_cluster = false\nlisten_addresses = ''\n" > /etc/postgresql-common/createcluster.conf
cluster_guard_written=1
stage=install
dpkg -i --force-confold '--path-exclude=/dev/*' "$work"/debs/*.deb > "$work/dpkg.log" 2>&1
assert_interop_fenced
test -z "$(pg_lsclusters --no-header)"
assert_no_pg_tcp
test "$(/usr/lib/postgresql/16/bin/postgres --version)" = 'postgres (PostgreSQL) 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)'
pg_createcluster 16 ara_m1 --port 55432 --socketdir=/var/run/postgresql --start-conf=manual -- --auth-local=peer --auth-host=scram-sha-256 > "$work/create.log" 2>&1
cat > "$conf/pg_hba.conf" <<'HBA'
local all postgres peer
local all all scram-sha-256
host all all 0.0.0.0/0 reject
host all all ::/0 reject
HBA
chown postgres:postgres "$conf/pg_hba.conf"
chmod 640 "$conf/pg_hba.conf"
printf "\nlisten_addresses = ''\npassword_encryption = 'scram-sha-256'\nshared_buffers = '128MB'\nmax_connections = 20\n" >> "$conf/postgresql.conf"
# Every Pg process inherits this cgroup, including after crash recovery.
test "$(stat -fc %T /sys/fs/cgroup)" = cgroup2fs
grep -qw memory /sys/fs/cgroup/cgroup.controllers
grep -qw cpu /sys/fs/cgroup/cgroup.controllers
printf '+memory +cpu' > /sys/fs/cgroup/cgroup.subtree_control
mkdir /sys/fs/cgroup/ara-stage1
printf 1073741824 > /sys/fs/cgroup/ara-stage1/memory.max
printf '100000 100000' > /sys/fs/cgroup/ara-stage1/cpu.max
printf '+memory +cpu' > /sys/fs/cgroup/ara-stage1/cgroup.subtree_control
mkdir "$cg"
printf 1073741824 > "$cg/memory.max"
printf 0 > "$cg/memory.swap.max"
printf '100000 100000' > "$cg/cpu.max"
start_pg() {
  (printf '%s' "$BASHPID" > "$cg/cgroup.procs"; exec su -s /bin/sh postgres -c 'pg_ctlcluster --skip-systemctl-redirect 16 ara_m1 start') > "$work/start.log" 2>&1
  pg_started=1
  pg_isready -h /var/run/postgresql -p 55432 -t 5 > /dev/null
  assert_no_pg_tcp
}
check_group() {
  test "$(cat "$cg/memory.max")" = 1073741824
  test "$(cat "$cg/memory.swap.max")" = 0
  test "$(cat "$cg/cpu.max")" = '100000 100000'
  for pid in $(pgrep -x postgres); do grep -qx '0::/ara-stage1/pg' "/proc/$pid/cgroup"; done
  test "$(awk '$1=="oom"||$1=="oom_kill"{n+=$2}END{print n+0}' "$cg/memory.events")" -eq 0
  printf 'CGROUP_SAMPLE current=%s peak=%s cpu=%s\n' "$(cat "$cg/memory.current")" "$(cat "$cg/memory.peak")" "$(cat "$cg/cpu.max")"
  printf 'CGROUP_EVENTS_BEGIN\n'; cat "$cg/memory.events"; printf 'CGROUP_EVENTS_END\n'
}
stage=start
start_pg
stage=provision
admin() { su -s /bin/sh postgres -c "psql -X -q -w -v ON_ERROR_STOP=1 -h /var/run/postgresql -p 55432 $*"; }
id ara_qualify >/dev/null 2>&1 && exit 61
useradd --system --no-create-home --shell /usr/sbin/nologin ara_qualify
install -d -o ara_qualify -g ara_qualify -m700 /var/lib/ara-m1 "$secret"
sql="$work/roles-private.sql"
chmod 700 "$work"
printf 'CREATE ROLE ara_m1_migration NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;\nCREATE DATABASE ara_m1 OWNER ara_m1_migration;\nCREATE DATABASE ara_m1_test OWNER ara_m1_migration;\n' > "$sql"
for role in ara_m1_app ara_m1_checkpoint ara_m1_test; do
  password=$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')
  test "${#password}" -eq 64
  printf "CREATE ROLE %s LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '%s';\n" "$role" "$password" >> "$sql"
  db=ara_m1; [ "$role" != ara_m1_test ] || db=ara_m1_test
  printf '/var/run/postgresql:55432:*:%s:%s\n' "$role" "$password" > "$secret/$role.pgpass"
  unset password
  chown ara_qualify:ara_qualify "$secret/$role.pgpass"; chmod 600 "$secret/$role.pgpass"
done
cat >> "$sql" <<'SQL'
REVOKE CONNECT, TEMP ON DATABASE ara_m1 FROM PUBLIC;
REVOKE CONNECT, TEMP ON DATABASE ara_m1_test FROM PUBLIC;
GRANT CONNECT ON DATABASE ara_m1 TO ara_m1_app, ara_m1_checkpoint;
GRANT CONNECT ON DATABASE ara_m1_test TO ara_m1_test;
\connect ara_m1
REVOKE ALL ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA ara AUTHORIZATION ara_m1_migration;
CREATE SCHEMA ara_checkpoint AUTHORIZATION ara_m1_migration;
CREATE SCHEMA ara_negative AUTHORIZATION ara_m1_migration;
GRANT USAGE ON SCHEMA ara TO ara_m1_app;
GRANT USAGE ON SCHEMA ara_checkpoint TO ara_m1_checkpoint;
CREATE TABLE ara.qualification_witness(id int PRIMARY KEY, marker text NOT NULL);
ALTER TABLE ara.qualification_witness OWNER TO ara_m1_migration;
GRANT SELECT, INSERT ON ara.qualification_witness TO ara_m1_app;
INSERT INTO ara.qualification_witness VALUES(1,'ENV-M1-01-rebuild-20261108');
\connect ara_m1_test
REVOKE ALL ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA ara AUTHORIZATION ara_m1_migration;
CREATE SCHEMA ara_negative AUTHORIZATION ara_m1_migration;
GRANT USAGE ON SCHEMA ara TO ara_m1_test;
SQL
# postgres must traverse only this one public-to-it provisioning file, not credentials.
install -o postgres -g postgres -m600 "$sql" /var/lib/postgresql/ara-rebuild-roles.sql
admin '-d postgres -f /var/lib/postgresql/ara-rebuild-roles.sql' > "$work/provision.log" 2>&1
rm -f "$sql" /var/lib/postgresql/ara-rebuild-roles.sql
# Probe SQL is public, but its parent directory is intentionally private.
install -o postgres -g postgres -m644 "$work/role_probe.sql" /var/lib/postgresql/ara-rebuild-probe.sql
stage=roles_and_auth
check_group
cp "$cg/memory.events" "$work/memory-events-before"
query() {
  local role=$1 db=$2 query=$3
  # Query texts below are fixed qualification statements, never secrets.
  su -s /bin/sh ara_qualify -c "PGPASSFILE=$secret/$role.pgpass psql -X -q -w -v ON_ERROR_STOP=1 -h /var/run/postgresql -p 55432 -U $role -d $db -c '$query'"
}
expect_denied() {
  local label=$1 role=$2 db=$3 query=$4
  if query "$role" "$db" "$query" > "$work/negative.log" 2>&1; then echo "UNEXPECTED_PERMISSION=$label"; exit 62; fi
  grep -q 'permission denied' "$work/negative.log"
  printf 'DENIED=%s\n' "$label"
}
for role in ara_m1_app ara_m1_checkpoint ara_m1_test; do
  db=ara_m1; other=ara_m1_test; own=ara
  [ "$role" != ara_m1_checkpoint ] || own=ara_checkpoint
  if [ "$role" = ara_m1_test ]; then db=ara_m1_test; other=ara_m1; fi
  su -s /bin/sh ara_qualify -c "PGPASSFILE=$secret/$role.pgpass psql -X -q -w -v ON_ERROR_STOP=1 -h /var/run/postgresql -p 55432 -U $role -d $db -v expected_db=$db -v expected_role=$role -v own_schema=$own -v other_schema=ara_negative -v other_db=$other -f /var/lib/postgresql/ara-rebuild-probe.sql" > "$work/probe-$role.txt" 2>&1
  test "$(grep -Ec '^ *true *\|' "$work/probe-$role.txt")" -eq 15
  ! grep -Eq '^ *false *\|' "$work/probe-$role.txt"
  expect_denied "$role-ddl" "$role" "$db" "CREATE TABLE $own.forbidden(id int)"
  expect_denied "$role-temp" "$role" "$db" 'CREATE TEMP TABLE forbidden(id int)'
  expect_denied "$role-schema" "$role" "$db" 'CREATE SCHEMA forbidden'
  expect_denied "$role-cross-db" "$role" "$other" 'SELECT 1'
  expect_denied "$role-other-schema" "$role" "$db" 'SELECT * FROM ara_negative.forbidden'
  if su -s /bin/sh ara_qualify -c "PGPASSWORD=deliberately_wrong PGPASSFILE=/dev/null psql -X -q -w -h /var/run/postgresql -p 55432 -U $role -d $db -c 'SELECT 1'" > "$work/wrong-password.log" 2>&1; then exit 63; fi
  grep -q 'password authentication failed' "$work/wrong-password.log"
  printf 'ROLE_AND_AUTH_OK=%s checks=15\n' "$role"
done
if su -s /bin/sh ara_qualify -c "psql -X -q -w -h /var/run/postgresql -p 55432 -U postgres -d postgres -c 'SELECT 1'" > "$work/peer-negative.log" 2>&1; then exit 64; fi
grep -q 'Peer authentication failed' "$work/peer-negative.log"
test "$(admin "-d postgres -At -c \"SELECT rolcanlogin FROM pg_roles WHERE rolname='ara_m1_migration'\"")" = f
query ara_m1_app ara_m1 'SELECT pg_sleep(1)' > "$work/connection1.log" 2>&1 & p1=$!
query ara_m1_app ara_m1 'SELECT pg_sleep(1)' > "$work/connection2.log" 2>&1 & p2=$!
wait "$p1"; wait "$p2"
query ara_m1_app ara_m1 'INSERT INTO ara.qualification_witness VALUES(2, md5(random()::text))' > /dev/null
check_group
cp "$cg/memory.events" "$work/memory-events-before-crash"
stage=recovery
pid=$(head -n1 "$data/postmaster.pid")
test "$(cat /proc/"$pid"/comm)" = postgres
kill -KILL "$pid"
for i in $(seq 1 30); do if ! pgrep -x postgres >/dev/null; then break; fi; sleep 1; done
! pgrep -x postgres >/dev/null
start_pg
test "$(query ara_m1_app ara_m1 'COPY (SELECT count(*) FROM ara.qualification_witness) TO STDOUT')" = 2
check_group
cp "$cg/memory.events" "$work/memory-events-after-crash"
cmp "$work/memory-events-before" "$work/memory-events-before-crash"
cmp "$work/memory-events-before" "$work/memory-events-after-crash"
pg_ctlcluster --skip-systemctl-redirect 16 ara_m1 stop -m fast > "$work/stop.log" 2>&1
pg_started=0
! pgrep -x postgres >/dev/null
assert_no_pg_tcp
test -d "$data"
test -f "$secret/ara_m1_app.pgpass"
rm -f /var/lib/postgresql/ara-rebuild-probe.sql
assert_interop_fenced
printf 'PG_QUALIFICATION_OK\n'
