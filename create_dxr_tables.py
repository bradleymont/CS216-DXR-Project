from build_search_data_structure import build_search_data_structure
from collections import defaultdict

# converts ipaddr("1.2.3.4") to "1.2"
def get_first_16_bits_str(ip_addr):
    first_2_bytes_list = str(ip_addr).split(".")[:2]
    return ".".join(first_2_bytes_list)

# converts ipaddr("1.2.3.4") to "3.4"
def get_last_16_bits_str(ip_addr):
    last_2_bytes_list = str(ip_addr).split(".")[2:]
    return ".".join(last_2_bytes_list)

# converts 16 to '0000000000000010000'
def convert_int_to_19_bits(offset_int):
    return f'{offset_int:019b}'

def convert_int_to_12_bits(offset_int):
    return f'{offset_int:012b}'

def convert_bin_string_to_hex(bin_str):
    return '{:0{width}x}'.format(int(bin_str,2), width=8)

def increment_prefix(prefix):
    if prefix == "255.255":
        return "STOP"

    upper_byte, lower_byte = prefix.split(".")
    if lower_byte != "255":
        lower_byte = str(int(lower_byte) + 1)
    else:
        upper_byte = str(int(upper_byte) + 1)
        lower_byte = "0"
    
    return upper_byte + "." + lower_byte

def group_by_first_16_bits(interval_to_next_hop):

    # map each 16-bit prefix to a list of all the entries matching that 16-bit prefix
    prefix_to_entries = defaultdict(list)

    for ip_addr in interval_to_next_hop:
        first_16_bits_str = get_first_16_bits_str(ip_addr)
        prefix_to_entries[first_16_bits_str].append(ip_addr)

    return prefix_to_entries

def build_next_hop_table(interval_to_next_hop):
    # maps each next hop to its offset in the next hop table
    # the first entry at offset 0 is reserved for packets to be dropped
    next_hop_to_offset = dict()
    next_hop_to_offset["DROP"] = 0

    # next_hop table
    next_hop_table = ["DROP"]

    curr_offset = 1
    for next_hop in interval_to_next_hop.values():
        if next_hop not in next_hop_to_offset:
            next_hop_to_offset[next_hop] = curr_offset
            next_hop_table.append(next_hop)
            curr_offset += 1

    return next_hop_to_offset


def build_lookup_table(prefix_to_entries, interval_to_next_hop, next_hop_to_offset):

    lookup_table = dict()

    prefix_keys = list(prefix_to_entries.keys())

    prefix_keys.append("STOP")

    curr_offset_into_L2 = 0

    i = 0
    for i in range(len(prefix_keys) - 1):
        curr_prefix = prefix_keys[i]
        next_prefix = prefix_keys[i+1]

        matching_entries_list = prefix_to_entries[curr_prefix]

        lookup_table_val_bin = None

        # special case of 1 LSB that covers the whole range (0.0): go straight to L3
        if len(matching_entries_list) == 1 and get_last_16_bits_str(matching_entries_list[0]) == "0.0":
            next_hop = interval_to_next_hop[matching_entries_list[0]]
            offset_into_L3 = next_hop_to_offset[next_hop]
            offset_19_bits = convert_int_to_19_bits(offset_into_L3)

            lookup_table_val_bin = ("0" * 13) + offset_19_bits
            lookup_table_val_hex = convert_bin_string_to_hex(lookup_table_val_bin)
        else:
            num_unique_LSBs = len(matching_entries_list)
            num_unique_LSBs_12_bit = convert_int_to_12_bits(num_unique_LSBs)

            offset_into_L2_19_bit = convert_int_to_19_bits(curr_offset_into_L2)
            curr_offset_into_L2 += num_unique_LSBs

            lookup_table_val_bin = "0" + num_unique_LSBs_12_bit + offset_into_L2_19_bit

        lookup_table_val_hex = convert_bin_string_to_hex(lookup_table_val_bin)
        
        while curr_prefix != next_prefix:
            lookup_table[curr_prefix] = lookup_table_val_hex
            curr_prefix = increment_prefix(curr_prefix)

    return lookup_table


def main():
    interval_to_next_hop = build_search_data_structure()

    prefix_to_entries = group_by_first_16_bits(interval_to_next_hop)

    next_hop_to_offset = build_next_hop_table(interval_to_next_hop)

    lookup_table = build_lookup_table(prefix_to_entries, interval_to_next_hop, next_hop_to_offset)

    
    # print first 10 entries of lookup table
    i = 0
    for key in lookup_table:
        if i == 10: break
        print(key, lookup_table[key])
        i += 1

if __name__ == "__main__":
    main()