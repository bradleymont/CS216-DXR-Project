# L1 input 16 bits, output 32 bits
0 (i.e. 0.0): 0,12w0,19w0 // special 12bit 0 makes 19 bits offset into L3
1 (i.e. 0.1): 0,12w0,19w0 // repeats entry 0
2 (i.e. 0.2): 0,12w0,19w0 // repeats entry 0
...
// repeats up to entry 254
1*255 (i.e. 1.0): 0,12w0,19w1 // offset into L3
// 256 (1.1) repeats 255
257 (i.e. 1.2): 0,12w3,19w0 // not short type, make 3 entries in L2 starting at offset 0
258 (1.3): 0,12w0, 19w1
// 259-511 repeat 258
2*255 (i.e. 2.0): 0,12w0,19w0

# L2 input 19 bits, output 32 bits
0: 16w0 (i.e. 0.0), 16w2 // offset into L3
1: 16w(3*255+0) (i.e. 3.0), 16w3
2: 16w(4*255+0) (i.e. 4.0), 16w2

# L3: input 16 bits, output 32 bits
0: next hop of A as an ip address
1: next hop of B as an ip address
2: next hop of C as an ip address
3: next hop of D as an ip address
