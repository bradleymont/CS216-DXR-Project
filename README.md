# Testing & Running
TODO: recally how testing and running worked

# Headers
- `ethernet_t`: needed as packets are sent on mininet over ethernet
	- `dstAddr`: ignore
	- `srcAddr`: ignore
- `ipv4_t`: perform actual switching
	- `srcAddr`: gets SET to next hop (ignore name)
	- `dstAddr`: gets READ, to match on prefix tables

Q: where exactly does next hop ip address get put?
A: in **ipv4.srcAddr**.

# Topology
```
   port 1 	   port 2
h1 =======> switch =======> h2
		   port 3
		   =======> h3
		   port 4
		   =======> h4
		   port 5
		   =======> h5
		   port 6
		   =======> h6

h2 mac is 08:00:00:00:02:22
h3 mac is 08:00:00:00:03:33
h4 mac is 08:00:00:00:04:44
h5 mac is 08:00:00:00:05:55
h6 mac is 08:00:00:00:06:66
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
Direct lookup -> next hop entries (one of 65k):
```
{
	"table": "MyIngress.%%TABLE_NAME%%",
	"match": {
		"hdr.ipv4.dstAddr": [%%IP_ENTRY_IN_TABLE%%]
	},
	"action_name": "MyIngress.exact_set_next_hop",
	"action_params": {
		"nextHop": "%%IP_NEXT_HOP_IN_TABLE%%",
		"dstAddr": "08:00:00:00:02:22",
		"port": "2"
	}
},
```
