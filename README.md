# CS216 P4 Project

See our report
[here](https://docs.google.com/document/d/1jsXUteixMXiwWtKG3EKOCcSrPSZ_2mtfByLeMBqN0jM/edit)  

## Usage
```
> make clean && make # assuming you have the behavioral model and openflow set up correctly
mininet> h2 ./receive.py &
mininet> h1 ./send.py [QUERY]
mininet> h2 sync # no-op to force flush of stdout
```

# Headers
- `ethernet_t`: needed as packets are sent on mininet over ethernet
	- `dstAddr`: ignore
	- `srcAddr`: ignore
- `ipv4_t`: perform actual switching
	- `srcAddr`: ignore
	- `dstAddr`: READ to match on prefix tables, SET to resulting next hop
        - technically packet dies after this one hop but whatevers

Q: where does next hop ip address get put?
A: in **ipv4.dstAddr**.


# Topology
```
   port 1 	       port 2
h1 =======> switch =======> h2

h2 mac is 08:00:00:00:02:22
```

# Runtime table
Constant head/tail:
```
{
  "target": "bmv2",
  "p4info": "build/basic.p4.p4info.txt",
  "bmv2_json": "build/basic.json",
  "table_entries": [
	...
  ]
}
```
L1 table:
```
{
	"table": "MyVerifyChecksum.L1",
	"match": {
		"meta.ip_H": first 16 bits (e.g. 0x7F00 for 127.0)
	},
	"action_name": "MyIngress.L1_entry",
	"action_params": {
    // probably wanna pack it as one 4byte word
        "flag": "%%1_OR_0%%",
        "size": "%%12_BIT_INT%%",
        "offset": "%%19_BIT_INT%%"
	}
},
```
L2 table:
```
{
	"table": "MyIngress.L2",
	"match": {
		"offset": %%MONOTONIC_INDEX%%
	},
	"action_name": "MyIngress.L2_entry",
	"action_params": {
    // probably want to pack it as one 4byte word
        "flag": "%%1_OR_0%%",
        "size": "%%12_BIT_INT%%",
        "offset": "%%19_BIT_INT%%"
	}
},
```
L3 table:
```
{
	"table": "MyEgress.L3",
	"match": {
		"offset": %%MONOTONIC_INDEX%%
	},
	"action_name": "MyIngress.L3_entry",
	"action_params": {
        "ip": "%%NEXT_HOP_IP%%"
	}
},
```

# Implementation
## Metadata passed:
```
// break down ip address in parser stage
struct metadata_parse_ingress {
    bit<16> ip_H; // higher 16 bits
    bit<16> ip_L; // lower 16 bits
}
```
## Notes:
trick: table applies should go into other variables
then chain multiple applies based on the variables

## Pipeline:
- actual can only go in apply blocks
- use preamble to apply to define tables and actions (functions)

## parser:
- cannot overwrite incoming values in parser

## Ingress:
- only place ETHERNET forwarding logic works fully correctly
- can only apply tables once, resubmit to loop

## Egress block:
- cannot change egress port in egress block
- CAN change ipv4 srcaddr (which is basically all we care about)

## Mininet console:
usage: `[host] ./send.py [dest] [message]`  
can also do `[host] ./receive.py &`  
and then `[host] fg` to recover whatever packet was there
