// i am bad at converting ip address to decimal

# L1 input 16 bits, output 32 bits
// if entries don't exist, just ignore
// key is first 2 bytes of ip
0 (i.e. 0.0): 0,12w0,19w0 // special 12bit 0 makes 19 bits offset into L3
1 (i.e. 0.1): 0,12w0,19w0 // repeats entry 0
2 (i.e. 0.2): 0,12w0,19w0 // repeats entry 0
...
// repeats up to entry 254
1*255+1 (i.e. 1.0): 0,12w0,19w1 // offset into L3
// 256 (1.1) repeats 255
258 (i.e. 1.2): 0,12w3,19w0 // not short type, make 3 entries in L2 starting at offset 0
259 (1.3): 0,12w0, 19w1
// 260-511 repeat 258
2*255+1 (i.e. 2.0): 0,12w0,19w0

# L2 input 19 bits, output 32 bits
// insert exactly as in prefix start table; no extras needed
0: 16w0 (i.e. 0.0), 16w2 // offset into L3
1: 16w(3*255+1) (i.e. 3.0), 16w3
2: 16w(4*255+1) (i.e. 4.0), 16w2

# L3: input 16 bits, output 32 bits
0: next hop of A as an ip address
1: next hop of B as an ip address
2: next hop of C as an ip address
3: next hop of D as an ip address


# The example table in p4 runtime json
```
{
  "target": "bmv2",
  "p4info": "build/basic.p4.p4info.txt",
  "bmv2_json": "build/basic.json",
  "table_entries": [
      { "table": "MyIngress.L1",
        "match": { "meta.ip_H": "0000" },
        "action_name": "MyIngress.L1_respond",
        "action_params": { "ans": "00000001" }
      },
      { "table": "MyIngress.L1",
        "match": { "meta.ip_H": "0100" },
        "action_name": "MyIngress.L1_respond",
        "action_params": { "ans": "00000002" }
      },
      { "table": "MyIngress.L1",
        "match": { "meta.ip_H": "0102" },
        "action_name": "MyIngress.L1_respond",
        "action_params": { "ans": "02000000" }
      },
      { "table": "MyIngress.L1",
        "match": { "meta.ip_H": "0103" },
        "action_name": "MyIngress.L1_respond",
        "action_params": { "ans": "00000002" }
      },
      { "table": "MyIngress.L1",
        "match": { "meta.ip_H": "0200" },
        "action_name": "MyIngress.L1_respond",
        "action_params": { "ans": "00000001" }
      },
      { "table": "MyIngress.L2",
        "match": { "m": 0 },
        "action_name": "MyIngress.L2_respond",
        "action_params": { "ans": "00000003" }
      },
      { "table": "MyIngress.L2",
        "match": { "m": 1 },
        "action_name": "MyIngress.L2_respond",
        "action_params": { "ans": "03000004" }
      },
      { "table": "MyIngress.L2",
        "match": { "m": 2 },
        "action_name": "MyIngress.L2_respond",
        "action_params": { "ans": "04000003" }
      },
      { "table": "MyIngress.L2",
        "match": { "m": 3 },
        "action_name": "MyIngress.L2_respond",
        "action_params": { "ans": "ffff0003" }
      },
      { "table": "MyEgress.L3",
        "match": { "meta.ip_L": 1 },
        "action_name": "MyEgress.L3_respond",
        "action_params": { "ans": "0.0.0.0" }
      },
      { "table": "MyEgress.L3",
        "match": { "meta.ip_L": 2 },
        "action_name": "MyEgress.L3_respond",
        "action_params": { "ans": "0.0.0.1" }
      },
      { "table": "MyEgress.L3",
        "match": { "meta.ip_L": 3 },
        "action_name": "MyEgress.L3_respond",
        "action_params": { "ans": "0.0.0.2" }
      },
      { "table": "MyEgress.L3",
        "match": { "meta.ip_L": 4 },
        "action_name": "MyEgress.L3_respond",
        "action_params": { "ans": "0.0.0.3" }
      }
  ]
}
```

## notes on sample:
- l1 keys are ip addresses; l2, l3 keys are monotonically increasing integers (not hex)
- ans is always hex-encoded 32 bits as a string! no 0x..., just 8 characters `[0-9][a-f]`
- if a key must exist in l1 or l2 but no route exists, the 0 key in l3 specifies drop.
- when l1 does not skip straight to l3 and specifies an l2 range, the l2 range
    must have `0.0` and `255.255` entries (see previous note for missing routes)
    - the `255.255` entry copies the next hop/drop of the highest entry
    - the `0.0` entry copies:
        - the next hop/drop of the l1 entry directly previous to the l1 entry
            that led to the l2 entry;
        - the last hop/drop of the `255.255` entry in the l2 range specified by
            the l1 entry directly previous to this l1 entry
    - if a prefix has `a` unique LSBs, it can have:
        - `a+1` L2 entries (add `255.255`)
        - `a+2` L2 entries (also add `0.0`)
    - if `a` is 1, we can still have 3 entries in L2:
        - `0.0` points to 0 (drop)
        - `LSBs` points to next hop
        - `255.255` points to next hop
        - if the LSB is `0.0`, then use the direct lookup to l3
