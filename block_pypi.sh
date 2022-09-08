#!/bin/bash
set -o errexit -o nounset -o pipefail

ipv4addresses=$(dig pypi.org A +short)
ipv6addresses=$(dig pypi.org AAAA +short)
for addr in $ipv4addresses; do iptables -A OUTPUT -j DROP -d $addr; done
for addr in $ipv6addresses; do ip6tables -A OUTPUT -j DROP -d $addr; done
