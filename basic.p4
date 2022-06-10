/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#define PKT_INSTANCE_TYPE_NORMAL 0
#define PKT_INSTANCE_TYPE_RESUBMIT 6

const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
 *********************** H E A D E R S  ***********************************
 *************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

struct metadata {
    bit<16> ip_H;
    bit<16> ip_L; // or L3 query
    @field_list(1)
    bit<19> l;
    @field_list(1)
    bit<19> r;
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
}

/*************************************************************************
 *********************** P A R S E R  ***********************************
 *************************************************************************/

parser MyParser(packet_in packet,
        out headers hdr,
        inout metadata meta,
        inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.ip_H = hdr.ipv4.dstAddr[31:16];
        meta.ip_L = hdr.ipv4.dstAddr[15:0];
        transition accept;
    }

}

/*************************************************************************
 ************   C H E C K S U M    V E R I F I C A T I O N   *************
 *************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}


/*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

control MyIngress(inout headers hdr, inout metadata meta,
        inout standard_metadata_t standard_metadata) {

    bit<32> tmp = 0;
    bit<19> m;

    action drop() { mark_to_drop(standard_metadata); exit; }
    action set_forwarding() {
        standard_metadata.egress_spec = 2;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = 48w0x080000000222;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action L1_respond(bit<32> ans) { tmp = ans; }

    table L1 { key = { meta.ip_H : exact; }
        actions = { L1_respond; drop; }
        size = 65536;
        default_action = drop();
    }

    action L2_respond(bit<32> ans) { tmp = ans; }

    table L2 { key = { m : exact; }
        actions = { L2_respond; drop; }
        size = 524288;
        default_action = drop();
    }

/*
    table debug {
      key = { meta.r : exact; }
      actions = {}
    }
*/

    apply {
        if(standard_metadata.instance_type == PKT_INSTANCE_TYPE_NORMAL) {
            L1.apply();
            if(tmp[30:19] == 0) {
                meta.ip_L = tmp[15:0]; // only take 16 bc know first 3 must be 0
                set_forwarding(); 
                exit; // idiom for forward and exit
            }
            meta.l = tmp[18:0]; //inclusive
            meta.r = (meta.l + (bit<19>)tmp[30:19]) - 1; //inclusive
            resubmit_preserving_field_list(1); 
            exit; // idiom for restart and resubmit
        }

        //debug.apply();

        m = (bit<19>)(((bit<20>)meta.l + (bit<20>)meta.r) >> 1); // (r+l)/2 wo overflow
        if (meta.l >= meta.r)
            drop();

        L2.apply();

        // exact match or end of search
        if(meta.r == meta.l + 1 || meta.ip_L == tmp[31:16]) {
            meta.ip_L = tmp[15:0];
            set_forwarding();
            exit;
        }
        if(meta.ip_L < tmp[31:16])
            meta.r = m;
        else 
            meta.l = m;
        resubmit_preserving_field_list(1);
    }
}


/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr, inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    action L3_respond(ip4Addr_t ans) { hdr.ipv4.dstAddr = ans; }
    table L3 {
        key = { meta.ip_L : exact; } //using meta.ip_L as offset into L3 table
        actions = { L3_respond; }
        size = 65536;
    }

    apply { 
        L3.apply();
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
        update_checksum(
        hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
