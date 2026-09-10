---
name: wsl-dns-and-host-firewall
description: WSL2 Ubuntu-24.04 DNS was dead because systemd-resolved had no upstream; also the Windows host blocks all WSL->host traffic.
metadata:
  type: project
---

Fixed 2026-09-09. Two independent WSL network faults on this machine (`Ubuntu-24.04`, WSL 2.9.8.0, `networkingMode=nat`):

**1. DNS was completely broken (fixed).** Raw IP always worked (`ping 1.1.1.1`, `curl https://1.1.1.1` = 301) — only name resolution failed. Cause was a three-way config gap:
- `/etc/wsl.conf` has `[network] generateResolvConf = false`, so WSL never writes `/etc/resolv.conf`.
- `/etc/resolv.conf` symlinks to systemd-resolved's stub (`nameserver 127.0.0.53`).
- `systemd-networkd` is **disabled/inactive**, so no DHCP client ever handed systemd-resolved an uplink. `resolvectl status` showed zero DNS servers and `Link 2 (eth0): Current Scopes: none`.

Net effect: every lookup went to 127.0.0.53, which had nowhere to forward. Fix = give resolved a static upstream at
`/etc/systemd/resolved.conf.d/99-wsl-dns.conf` → `DNS=1.1.1.1 1.0.0.1 8.8.8.8`, `FallbackDNS=9.9.9.9 8.8.4.4`.
Persistent: file is on disk, `systemd-resolved` is `enabled`, and `generateResolvConf=false` means WSL won't clobber resolv.conf.

**2. Windows host blocks ALL WSL->host traffic (still open).** The NAT gateway `172.25.240.1` answers nothing — ICMP, tcp/53, and tcp/445 all time out (445 proving a firewall, since Windows always listens there). There are **no `WSL` Windows Firewall rules at all**, only Hyper-V ones, and all three profiles are enabled. Consequences:
- WSL cannot use the host DNS proxy, which is *why* the normal WSL DNS path was unavailable and why static public resolvers were the right fix.
- Public DNS means **no corporate/VPN split-DNS** resolution from WSL. Fine for personal use; revisit if a VPN is ever needed.
- WSL also cannot reach dev servers listening on Windows. Needs an elevated inbound allow rule on the `vEthernet (WSL)` interface to fix.

Diagnostic gotcha: `$var` inside `wsl.exe -d X -- bash -lc '...'` from Git Bash gets eaten by interop — a `for p in 53 445` loop printed empty ports. Write literal values. See [[wsl-claude-config-mirror]].
