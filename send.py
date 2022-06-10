#!/usr/bin/env python3
import random
import socket
import sys

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

def main():

    if len(sys.argv)<2:
        print('usage: ./send.py IP_ADDRESS')
        exit(1)

    iface = get_if()

    print("sending on interface %s with dst %s" % (iface, sys.argv[1]))
    pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt /IP(dst=sys.argv[1]) / TCP(dport=1234, sport=random.randint(49152,65535)) / '_'
    sendp(pkt, iface=iface, verbose=False)


if __name__ == '__main__':
    main()
