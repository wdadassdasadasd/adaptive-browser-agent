#!/bin/bash
set -euo pipefail
trap 'rc=$?; printf "BOOTSTRAP_FAIL line=%s status=%s\n" "$LINENO" "$rc" >&2; for log in /tmp/ara-rebuild/simulation.txt /tmp/ara-rebuild/uris.txt; do if test -f "$log"; then tail -n60 "$log" >&2; fi; done; exit "$rc"' ERR
umask 077
if test -e /tmp/ara-rebuild; then
  test -d /tmp/ara-rebuild
  test "$(ls -A /tmp/ara-rebuild)" = "$(printf 'interop-denied.txt\ninterop-probe-03.exe\ninterop-probe.exe')"
else
  mkdir -m700 /tmp/ara-rebuild
fi
grep -q '^VERSION_ID="24.04"' /etc/os-release
grep -qx 'systemd=false' /etc/wsl.conf
grep -qx 'enabled=false' /etc/wsl.conf
test ! -e /mnt/c
if test -e /proc/sys/fs/binfmt_misc/WSLInterop; then
  test "$(head -n1 /proc/sys/fs/binfmt_misc/WSLInterop)" = disabled
fi
test -z "${WSL_INTEROP-}"
! command -v cmd.exe >/dev/null 2>&1
awk '$3 == "drvfs" {exit 1} $3 == "9p" {n++; if ($1 != "drivers" || $2 != "/usr/lib/wsl/drivers" || $4 !~ /^ro,/ || $4 !~ /(^|,)nosuid(,|$)/ || $4 !~ /(^|,)nodev(,|$)/ || $4 !~ /(^|,)aname=drivers;fmask=222;dmask=222(,|$)/) exit 1} END {if (n > 1) exit 1}' /proc/mounts
chmod 700 /tmp/ara-rebuild/interop-probe-03.exe
pe_status=0
/tmp/ara-rebuild/interop-probe-03.exe /? > /tmp/ara-rebuild/interop-denied-03.txt 2>&1 || pe_status=$?
test "$pe_status" -eq 126
grep -q 'Exec format error' /tmp/ara-rebuild/interop-denied-03.txt
if test -e /proc/sys/fs/binfmt_misc/WSLInterop; then
  test "$(head -n1 /proc/sys/fs/binfmt_misc/WSLInterop)" = disabled
fi
printf 'WINDOWS_PE_EXEC_REJECTED\n'
test "$(awk 'NR>1{n++}END{print n+0}' /proc/net/route)" -eq 0
test "$(ls /sys/class/net)" = lo
! grep -qiE 'ara|research|worker|agent' /etc/passwd
test ! -e /root/.ssh
test ! -e /root/.bash_history
! grep -qiE 'proxy|credential|token' /etc/environment
! grep -rqiE 'ara|research|worker' /etc/cron.d /etc/systemd/system 2>/dev/null
grep MemTotal /proc/meminfo
test "$(nproc)" -eq 1
test "$(awk 'NR>1{n++}END{print n+0}' /proc/swaps)" -eq 0
for entry in noble:8f6f71ae839c8cba390a7643fcbbdacddb0bc7d12c1583a2dd80a1f8443a30e5 noble-updates:caafce0abc3621247a817fc29dc0ccf2a58d9734119fe01b54e6c20a5ddce67f noble-security:e45480701a5ebc5163d91faa71e71d836c79cb084870639e4fdc8c67ac4afae0; do
  pocket=${entry%%:*}; hash=${entry#*:}
  stem=/var/lib/apt/lists/snapshot.ubuntu.com_ubuntu_20261021T000000Z_dists_$pocket
  printf '%s  %s\n' "$hash" "${stem}_Packages" | sha256sum -c -
  test ! -e "${stem}_main_binary-amd64_Packages"
  mv "${stem}_Packages" "${stem}_main_binary-amd64_Packages"
done
sha256sum /var/lib/dpkg/status > /tmp/ara-rebuild/status-before
find /var/lib/apt/lists -type f -exec sha256sum {} \; | sort > /tmp/ara-rebuild/lists-before
pins=(postgresql-16=16.15-0ubuntu0.24.04.1 postgresql-client-16=16.15-0ubuntu0.24.04.1 postgresql-common=257build1.1 postgresql-client-common=257build1.1 systemd=255.4-1ubuntu8.18 systemd-sysv=255.4-1ubuntu8.18)
options=(-o Debug::NoLocking=1 -o Dir::Cache::pkgcache= -o Dir::Cache::srcpkgcache=)
apt-get "${options[@]}" --print-uris -s -y install "${pins[@]}" > /tmp/ara-rebuild/simulation.txt 2>&1
apt-get "${options[@]}" --print-uris --download-only -y install "${pins[@]}" > /tmp/ara-rebuild/uris.txt 2>&1
test "$(wc -c < /tmp/ara-rebuild/uris.txt)" -le 4194304
sha256sum -c /tmp/ara-rebuild/status-before
find /var/lib/apt/lists -type f -exec sha256sum {} \; | sort > /tmp/ara-rebuild/lists-after
cmp /tmp/ara-rebuild/lists-before /tmp/ara-rebuild/lists-after
grep -q "^'https://snapshot.ubuntu.com/ubuntu/20261021T000000Z/pool/" /tmp/ara-rebuild/uris.txt
printf 'BOOTSTRAP_CHECKS_OK\n'
