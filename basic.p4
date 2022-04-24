/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

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
	/* empty */
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
		transition accept;
	}

}

/*************************************************************************
 ************   C H E C K S U M    V E R I F I C A T I O N   *************
 *************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
	apply {  }
}


/*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

control MyIngress(inout headers hdr,
		inout metadata meta,
		inout standard_metadata_t standard_metadata) {

	action drop() {
		mark_to_drop(standard_metadata);
	}

	// TODO: apply binary search on exact match (lookup) on every
	// inner node, which is also a table
	// populate leaf values, only 7 of them, last one is default
	// 3 tables
	// first two have key: ?a value: ?a 
	// last table has a different value (route)
	// ip addresses are sorted (???) 1-7
	// 7 nodes or leaves?? nodes would be 1 + 2 + 4

	// algo: eg. 10.0.0.1 - 10.0.0.8
	// take input header, get destination address (destaddr)
	// on 1st table (1 entry to 2 entry):
		// compare destaddr to branch value (4)
		// int table_1_offset_1
		// int table_3_offset_1,2,3,4
	// exact match on root node -> immediately exit
	// nodes are [(1, D1), (2, D2), ...] build binary search here?
	// first search: Q, 4 -> 
	

// table 1: key: 4 value: {next_hop: A4, left/right: pointer_to_table(?)}

// table 2.1: key: 2 value: {next_hop: A2, left/right: pointer_to_table(?)}

	// not matching -> send off to other table


	/*
	   table ipv4_lpm {
		   reads {
			   ipv4.dstAddr : 
			   lpm;
		   }

		   actions {
			   set_next_hop;
			   drop; 
		   }
	   } 

	   apply(l2_table);
	   if (valid(ipv4)) {
		   apply(ipv4_table);
	   }


    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: exact;
        }
	const entries = {
            TCP_OPTION_END_OF_OPTIONS: kind_only();
            TCP_OPTION_NOP:            kind_only();
            TCP_OPTION_MSS:            one_legal_length(4);
            TCP_OPTION_WINDOW_SCALE:   one_legal_length(4);
            TCP_OPTION_SACK_PERMITTED: one_legal_length(2);
            TCP_OPTION_SACK:           variable_length();
            TCP_OPTION_TIMESTAMPS:     one_legal_length(10);
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }
*/


// todo: figure out type
   action comparison() { ; }
   action set_next_hop() { ; }
    table l1_binsearch {
	key = {
	    hdr.ipv4.dstAddr : exact;
	}
	actions = {
	   set_next_hop;
	   comparison;
	}
	const entries = {
	    4 : set_next_hop();
	}
       const default_action = comparison; 
    }



	   

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    apply {
        if (hdr.ipv4.isValid()) {
            l1_binsearch.apply();
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
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
