#!/usr/bin/env python3
import random
import socket
import sys
import time

from scapy.all import IP, TCP, Ether, get_if_hwaddr, get_if_list, sendp


def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

def make_ip():
    return f"{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

def main():
    count = 0
    random.seed(42)
    iface = get_if()
    s = get_if_hwaddr(iface)

    t_end = time.time() + 60
    while time.time() < t_end:
        pkt = Ether(src=s, dst='ff:ff:ff:ff:ff:ff')
        pkt = pkt /IP(dst=make_ip()) / TCP(dport=1234, sport=random.randint(49152,65535)) / '_'
        sendp(pkt, iface=iface, verbose=False)
        count += 1

    print(f"blast: I sent a total of {count} packets")
    sys.stdout.flush()

if __name__ == '__main__':
    main()
