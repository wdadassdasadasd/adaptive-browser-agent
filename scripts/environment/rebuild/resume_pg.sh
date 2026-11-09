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
    case "$stage" in install) tail -c 8192 "$work/dpkg-resume-03.log" 2>/dev/null || true;; start|recovery) tail -c 8192 "$work/start-$stage-06.log" 2>/dev/null || true;; esac
  fi
  if [ "$pg_started" = 1 ]; then pg_ctlcluster --skip-systemctl-redirect 16 ara_m1 stop -m fast >/dev/null 2>&1 || true; fi
  [ "$guard_written" = 0 ] || rm -f /usr/sbin/policy-rc.d
  [ "$cluster_guard_written" = 0 ] || rm -f /etc/postgresql-common/createcluster.conf
  rm -f "$work/roles-private.sql" /var/lib/postgresql/ara-rebuild-roles.sql
  exit "$code"
}
trap cleanup EXIT
test -f "$work/resume-install-attempt-03"
test ! -e "$work/resume-auth-attempt-06"
test ! -e /usr/sbin/policy-rc.d
test ! -e /etc/postgresql-common/createcluster.conf
test -f "$work/resume-start-attempt-05"
test -d /var/lib/ara-m1/credentials
test "$(stat -c '%a:%U:%G' /var/lib/ara-m1/credentials)" = '700:ara_qualify:ara_qualify' 
if pgrep -x postgres >/dev/null; then exit 75; fi
test "$(pg_lsclusters --no-header | wc -l)" -eq 1
pg_lsclusters --no-header | awk '$1 != "16" || $2 != "ara_m1" || $3 != "55432" || $4 != "down" || $5 != "postgres" || $6 != "/var/lib/postgresql/16/ara_m1" {exit 1}'
for deb in "$work"/debs/*.deb; do
  package=$(dpkg-deb -f "$deb" Package)
  version=$(dpkg-deb -f "$deb" Version)
  test "$(dpkg-query -W -f='${Status}|${Version}' "$package")" = "install ok installed|$version"
done
test -z "$(dpkg --audit)"
test "$(cat "$conf/pg_hba.conf")" = "$(printf 'local all postgres peer\nlocal all all scram-sha-256\nhost all all 0.0.0.0/0 reject\nhost all all ::/0 reject')"
listen=$(su -s /bin/sh postgres -c '/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/16/ara_m1 -c config_file=/etc/postgresql/16/ara_m1/postgresql.conf -C listen_addresses')
test -z "$listen"
touch "$work/resume-auth-attempt-06"
# This approved cluster has no TCP listener; SCRAM/peer use its local socket.
# Disable only the unused TLS listener setting; preserve the failed certificate.
printf "\nssl = off\n" >> "$conf/postgresql.conf"
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
  test -L /var/run
  case "$(readlink /var/run)" in /run|../run) ;; *) exit 76;; esac
  test ! -L /run/postgresql
  install -d -o postgres -g postgres -m2775 /run/postgresql
  (printf '%s' "$BASHPID" > "$cg/cgroup.procs"; exec su -s /bin/sh postgres -c 'pg_ctlcluster --skip-systemctl-redirect 16 ara_m1 start') > "$work/start-$stage-06.log" 2>&1
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
stage=resume_auth
admin() { su -s /bin/sh postgres -c "psql -X -q -w -v ON_ERROR_STOP=1 -h /var/run/postgresql -p 55432 $*"; }
witness=$(admin '-d ara_m1 -At -c "SELECT count(*) FROM ara.qualification_witness"')
test "$witness" = 1
for role in ara_m1_app ara_m1_checkpoint ara_m1_test; do
  credential="$secret/$role.pgpass"
  test "$(stat -c '%a:%U:%G' "$credential")" = '600:ara_qualify:ara_qualify'
  awk -F: -v role="$role" 'NF != 5 || $1 != "/var/run/postgresql" || $2 != "55432" || $3 != "*" || $4 != role || length($5) != 64 || $5 ~ /[^0-9a-f]/ {exit 1} END {if(NR != 1) exit 1}' "$credential"
  test ! -e "$credential.before-06"
  cp -p "$credential" "$credential.before-06"
  su -s /bin/sh ara_qualify -c "sed -i 's|^/var/run/postgresql:|localhost:|' $credential"
  test "$(stat -c '%a:%U:%G' "$credential")" = '600:ara_qualify:ara_qualify'
  grep -q '^localhost:55432:' "$credential"
  cmp <(cut -d: -f2- "$credential.before-06") <(cut -d: -f2- "$credential")
done
install -o postgres -g postgres -m644 "$work/role_probe.sql" /var/lib/postgresql/ara-rebuild-probe-06.sql
stage=roles_and_auth
check_group
cp "$cg/memory.events" "$work/memory-events-06-before"
query() {
  local role=$1 db=$2 query=$3
  # Query texts below are fixed qualification statements, never secrets.
  su -s /bin/sh ara_qualify -c "PGPASSFILE=$secret/$role.pgpass psql -X -q -w -v ON_ERROR_STOP=1 -h /var/run/postgresql -p 55432 -U $role -d $db -c '$query'"
}
expect_denied() {
  local label=$1 role=$2 db=$3 query=$4
  if query "$role" "$db" "$query" > "$work/negative-06.log" 2>&1; then echo "UNEXPECTED_PERMISSION=$label"; exit 62; fi
  grep -q 'permission denied' "$work/negative-06.log"
  printf 'DENIED=%s\n' "$label"
}
for role in ara_m1_app ara_m1_checkpoint ara_m1_test; do
  db=ara_m1; other=ara_m1_test; own=ara
  [ "$role" != ara_m1_checkpoint ] || own=ara_checkpoint
  if [ "$role" = ara_m1_test ]; then db=ara_m1_test; other=ara_m1; fi
  su -s /bin/sh ara_qualify -c "PGPASSFILE=$secret/$role.pgpass psql -X -q -w -v ON_ERROR_STOP=1 -h /var/run/postgresql -p 55432 -U $role -d $db -v expected_db=$db -v expected_role=$role -v own_schema=$own -v other_schema=ara_negative -v other_db=$other -f /var/lib/postgresql/ara-rebuild-probe-06.sql" > "$work/probe-06-$role.txt" 2>&1
  test "$(grep -Ec '^ *true *\|' "$work/probe-06-$role.txt")" -eq 15
  ! grep -Eq '^ *false *\|' "$work/probe-06-$role.txt"
  expect_denied "$role-ddl" "$role" "$db" "CREATE TABLE $own.forbidden(id int)"
  expect_denied "$role-temp" "$role" "$db" 'CREATE TEMP TABLE forbidden(id int)'
  expect_denied "$role-schema" "$role" "$db" 'CREATE SCHEMA forbidden'
  expect_denied "$role-cross-db" "$role" "$other" 'SELECT 1'
  expect_denied "$role-other-schema" "$role" "$db" 'SELECT * FROM ara_negative.forbidden'
  if su -s /bin/sh ara_qualify -c "PGPASSWORD=deliberately_wrong PGPASSFILE=/dev/null psql -X -q -w -h /var/run/postgresql -p 55432 -U $role -d $db -c 'SELECT 1'" > "$work/wrong-password-06.log" 2>&1; then exit 63; fi
  grep -q 'password authentication failed' "$work/wrong-password-06.log"
  printf 'ROLE_AND_AUTH_OK=%s checks=15\n' "$role"
done
if su -s /bin/sh ara_qualify -c "psql -X -q -w -h /var/run/postgresql -p 55432 -U postgres -d postgres -c 'SELECT 1'" > "$work/peer-negative-06.log" 2>&1; then exit 64; fi
grep -q 'Peer authentication failed' "$work/peer-negative-06.log"
test "$(admin "-d postgres -At -c \"SELECT rolcanlogin FROM pg_roles WHERE rolname='ara_m1_migration'\"")" = f
query ara_m1_app ara_m1 'SELECT pg_sleep(1)' > "$work/connection1-06.log" 2>&1 & p1=$!
query ara_m1_app ara_m1 'SELECT pg_sleep(1)' > "$work/connection2-06.log" 2>&1 & p2=$!
wait "$p1"; wait "$p2"
query ara_m1_app ara_m1 'INSERT INTO ara.qualification_witness VALUES(2, md5(random()::text))' > /dev/null
check_group
cp "$cg/memory.events" "$work/memory-events-06-before-crash"
stage=recovery
pid=$(head -n1 "$data/postmaster.pid")
test "$(cat /proc/"$pid"/comm)" = postgres
kill -KILL "$pid"
for i in $(seq 1 30); do if ! pgrep -x postgres >/dev/null; then break; fi; sleep 1; done
if pgrep -x postgres >/dev/null; then exit 75; fi
start_pg
test "$(query ara_m1_app ara_m1 'COPY (SELECT count(*) FROM ara.qualification_witness) TO STDOUT')" = 2
check_group
cp "$cg/memory.events" "$work/memory-events-06-after-crash"
cmp "$work/memory-events-06-before" "$work/memory-events-06-before-crash"
cmp "$work/memory-events-06-before" "$work/memory-events-06-after-crash"
pg_ctlcluster --skip-systemctl-redirect 16 ara_m1 stop -m fast > "$work/stop-06.log" 2>&1
pg_started=0
if pgrep -x postgres >/dev/null; then exit 75; fi
assert_no_pg_tcp
test -d "$data"
test -f "$secret/ara_m1_app.pgpass"
rm -f /var/lib/postgresql/ara-rebuild-probe-06.sql
assert_interop_fenced
printf 'PG_RESUMED_QUALIFICATION_OK\n'
