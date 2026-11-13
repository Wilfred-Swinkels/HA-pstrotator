#!/usr/bin/env python3
"""Diagnostic tool: query PstRotator's native UDP interface for its real
azimuth/elevation and print the raw response.

Per the official PstRotator User's Manual (UDP Control section):
sending "<PST>AZ?</PST>" / "<PST>EL?</PST>" to the configured UDP port
makes PstRotator report "AZ:xxx.x<CR>" / "EL:yy.y<CR>" to UDP port + 1
(a *fixed* port, not back to the sender's source port) -- so this script
listens there, not on an arbitrary local port.

Usage (Python 3, no extra packages needed):

    python3 pstrotator_query_test.py                # uses 192.168.0.88:12000
    python3 pstrotator_query_test.py 192.168.0.88    # explicit host
    python3 pstrotator_query_test.py 192.168.0.88 12000
"""
from __future__ import annotations

import socket
import sys
import time

DEFAULT_HOST = "192.168.0.88"
DEFAULT_PORT = 12000
LISTEN_TIMEOUT = 5.0
COMMANDS = ["<PST>AZ?</PST>", "<PST>EL?</PST>"]


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    listen_port = port + 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("0.0.0.0", listen_port))
    except OSError as err:
        print(f"Could not bind UDP port {listen_port}: {err}")
        print("Is something else already using it (e.g. a running instance")
        print("of this integration)?")
        return
    sock.settimeout(LISTEN_TIMEOUT)

    print(f"Listening on UDP port {listen_port} (= command port {port} + 1)")
    print(f"Sending to {host}:{port} ...")
    for command in COMMANDS:
        sock.sendto(command.encode("ascii"), (host, port))
        print(f"  sent: {command}")

    print(f"\nListening for replies for {LISTEN_TIMEOUT:.0f}s ...\n")
    start = time.monotonic()
    packet_count = 0
    while time.monotonic() - start < LISTEN_TIMEOUT:
        remaining = LISTEN_TIMEOUT - (time.monotonic() - start)
        sock.settimeout(max(0.1, remaining))
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            break
        packet_count += 1
        print(f"--- packet {packet_count} from {addr[0]}:{addr[1]} ---")
        print("raw bytes:", repr(data))
        try:
            print("as ascii: ", data.decode("ascii"))
        except UnicodeDecodeError:
            print("as utf-8 (ascii decode failed):", data.decode("utf-8", errors="replace"))
        print()

    if packet_count == 0:
        print("No reply received within the timeout.")
        print("Check: is PstRotator running, is UDP Control enabled with")
        print(f"this port ({port}), and is inbound UDP on port {listen_port}")
        print("allowed through any firewall between this machine and PstRotator?")
    else:
        print(f"Done, received {packet_count} packet(s).")

    sock.close()


if __name__ == "__main__":
    main()
