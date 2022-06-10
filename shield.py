#!/usr/bin/env python3
import os
import sys
import time

from scapy.all import (
    TCP,
    FieldLenField,
    FieldListField,
    IntField,
    IPOption,
    ShortField,
    get_if_list,
    sniff,
    AsyncSniffer
)
from scapy.layers.inet import _IPOption_HDR

def get_if():
    ifs=get_if_list()
    iface=None
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

class IPOption_MRI(IPOption):
    name = "MRI"
    option = 31
    fields_desc = [ _IPOption_HDR,
                    FieldLenField("length", None, fmt="B",
                                  length_of="swids",
                                  adjust=lambda pkt,l:l+4),
                    ShortField("count", 0),
                    FieldListField("swids",
                                   [],
                                   IntField("", 0),
                                   length_from=lambda pkt:pkt.count*4) ]
def handle_pkt(pkt, x):
    if TCP in pkt and pkt[TCP].dport == 1234:
        pass

count = 0
def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]

    def l(x):
        global count
        handle_pkt(x, count)
        count += 1

    t_end = time.time() + 65
    t = AsyncSniffer(iface = iface, prn = l)
    t.start()
    print("5 seconds to start blasting...")
    sys.stdout.flush()
    time.sleep(65)
    t.stop()

    print(f"shield: I caught {count} packets")
    sys.stdout.flush()

if __name__ == '__main__':
    main()
