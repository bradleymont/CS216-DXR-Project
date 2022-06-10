import parse_bgptable
import ipaddress
from collections import defaultdict
import heapq

# returns a 3-tuple of IPv4Address objects representing the lower and upper bounds
# of the range represented by the IP prefix, and the prefix length
def convert_ip_prefix_string_to_range(ip_string):
    ip_string_list = ip_string.split('/')
    ip_addr = ip_string_list[0]

    # assume that no provided prefix means /32
    prefix_len = 32
    if len(ip_string_list) == 2:
        prefix_len = int(ip_string_list[1])

    # converts '192.168.1.1' to '11000000101010000000000100000001'
    def convert_ip_addr_to_bit_string(ip_addr):
        ip_addr_bit_string = ""

        ip_addr_int = int(ipaddress.IPv4Address(ip_addr))
        ip_addr_bytes = ip_addr_int.to_bytes(4, byteorder='big')
        for byte in ip_addr_bytes:
            byte_in_binary = str(bin(byte)[2:])
            ip_addr_bit_string += ('0' * (8 - len(byte_in_binary))) + byte_in_binary

        return ip_addr_bit_string
    
    ip_addr_bit_string = convert_ip_addr_to_bit_string(ip_addr)

    # get the lower end of the range by zero-ing out the last 32-prefix_len bits
    lower_end_of_range_bit_str = ip_addr_bit_string[:prefix_len] + ('0' * (32 - prefix_len))
    lower_end_of_range_int = int(lower_end_of_range_bit_str, 2)
    lower_end_of_range_ip_addr = ipaddress.IPv4Address(lower_end_of_range_int)

    # get the upper end of the range by one-ing out the last 32-prefix_len bits
    upper_end_of_range_bit_str = ip_addr_bit_string[:prefix_len] + ('1' * (32 - prefix_len))
    upper_end_of_range_int = int(upper_end_of_range_bit_str, 2)
    upper_end_of_range_ip_addr = ipaddress.IPv4Address(upper_end_of_range_int)

    # make the upper end exclusive by adding 1
    if upper_end_of_range_ip_addr < ipaddress.IPv4Address("255.255.255.255"):
        upper_end_of_range_ip_addr += 1

    return (lower_end_of_range_ip_addr, upper_end_of_range_ip_addr, prefix_len)

# converts data from the form (IP prefix string, next hop) to the form
# ((lower bound IPv4Address, upper bound IPv4Address, prefix_len), next hop)
# returns a set of all range boundary points 
def convert_table_entries_ranges(bgp_table_entries, range_start_to_bgp_entries):

    # initialize range boundaries set
    range_boundaries_set = set()
    range_boundaries_set.add(ipaddress.IPv4Address("0.0.0.0"))
    range_boundaries_set.add(ipaddress.IPv4Address("255.255.255.255"))
    
    for index, (ip_prefix, next_hop) in enumerate(bgp_table_entries):
        ip_prefix_range_form = convert_ip_prefix_string_to_range(ip_prefix)
        bgp_table_entries[index] = (ip_prefix_range_form, next_hop)

        # add lower and upper boundary to set
        range_boundaries_set.add(ip_prefix_range_form[0])
        range_boundaries_set.add(ip_prefix_range_form[1])

        # add to the minheap for its lower boundary in range_start_to_bgp_entries
        prefix_len = ip_prefix_range_form[2]
        heapq.heappush(range_start_to_bgp_entries[ip_prefix_range_form[0]], (prefix_len, bgp_table_entries[index]))

    return range_boundaries_set

def build_interval_to_next_hop_structure(range_boundaries, range_start_to_bgp_entries):
    interval_to_next_hop = dict()

    active_bgp_entries_stack = []

    for i in range(len(range_boundaries) - 1):
        range_lower_bound = range_boundaries[i] # inclusive
        range_upper_bound = range_boundaries[i+1] # exclusive

        # push all BGP entries to the stack that become active during this interval
        # push the shortest length prefix first

        # heap of all BGP entry ranges that start at the beginning of this range
        bgp_entries_starting_now = range_start_to_bgp_entries[range_lower_bound]

        while bgp_entries_starting_now:
            _, bgp_entry_with_shortest_prefix = heapq.heappop(bgp_entries_starting_now)
            active_bgp_entries_stack.append(bgp_entry_with_shortest_prefix)

        # find the BGP table entry with the longest prefix that contains the current interval
        # which is the BGP entry at the top of the stack

        if active_bgp_entries_stack:
            matching_bgp_table_entry = active_bgp_entries_stack[-1]
            matching_bgp_table_entry_next_hop = matching_bgp_table_entry[1]
            interval_to_next_hop[range_lower_bound] = matching_bgp_table_entry_next_hop
        else:
            # no matching entries in this interval
            interval_to_next_hop[range_lower_bound] = "DROP"

        # pop off all entries from the stack whose range ends in this interval
        if active_bgp_entries_stack:
            entry_at_top_of_stack = active_bgp_entries_stack[-1]
            entry_at_top_of_stack_range_end = entry_at_top_of_stack[0][1]
            while entry_at_top_of_stack_range_end <= range_upper_bound:
                active_bgp_entries_stack.pop()
                if not active_bgp_entries_stack:
                    break
                entry_at_top_of_stack = active_bgp_entries_stack[-1]
                entry_at_top_of_stack_range_end = entry_at_top_of_stack[0][1]

    return interval_to_next_hop

def merge_interval_to_next_hop_structure(interval_to_next_hop):
    merged_interval_to_next_hop = dict()

    # if it matches the previous, don't add it
    curr_next_hop = ""

    for ip_addr, next_hop in interval_to_next_hop.items():
        if next_hop == curr_next_hop:
            # don't add consecutive entries that map to the same next hop
            continue

        merged_interval_to_next_hop[ip_addr] = next_hop
        curr_next_hop = next_hop

    return merged_interval_to_next_hop

def build_search_data_structure():
    bgp_table_file_path = "bgptable.txt"
    #bgp_table_entries = parse_bgptable.parse_bgp_table_file(bgp_table_file_path)

    # sample data
    
    bgp_table_entries = [
        ('0.0.0.0/0', 'A'),
        ('1.0.0.0/8', 'B'),
        ('1.2.0.0/16', 'C'),
        ('1.2.3.0/24', 'D'),
        ('1.2.4.5', 'C')
    ]
    

    # maps the beginning range value to a minheap of all the
    # BGP table entries with that beginning range value
    range_start_to_bgp_entries = defaultdict(list)

    range_boundaries_set = convert_table_entries_ranges(bgp_table_entries, range_start_to_bgp_entries)

    # sort range boundaries
    range_boundaries = list(range_boundaries_set)
    range_boundaries.sort()

    interval_to_next_hop = build_interval_to_next_hop_structure(range_boundaries, range_start_to_bgp_entries)

    interval_to_next_hop = merge_interval_to_next_hop_structure(interval_to_next_hop)

    return interval_to_next_hop
