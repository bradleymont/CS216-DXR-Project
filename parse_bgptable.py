import re

# parses bgp table text file and returns list of bgp entries
# each element is a tuple of the form (IP prefix, next hop IP address)
def parse_bgp_table_file(bgp_table_file_path):
    with open(bgp_table_file_path) as f:
        file_lines = f.readlines()

    # remove header and footer information from BGP table
    # convert from list back to string
    file_string = "".join(file_lines[7:-4])

    # separate each prefix entry, using "i", "e", or "?" as the delimiter
    bgp_table_strings = re.split(r"i|e|\?", file_string)

    # convert each entry to list representation (splitting on white space)
    bgp_table_entries = list(map(lambda line_string: line_string.split(), bgp_table_strings))

    # each entry should contain an IP prefix and a next hop
    # remove entries that do not contain both by removing all entries
    #   that don't contain a string with a "." as its 3rd element
    def is_valid_entry(bgp_table_entry_list):
        return len(bgp_table_entry_list) >= 3 and "." in bgp_table_entry_list[2]

    bgp_table_entries = list(filter(is_valid_entry, bgp_table_entries))   

    # convert each entry to a tuple representation: (IP prefix, next hop)
    def convert_entry_to_prefix_nexthop_pair(entry):
        prefix = entry[1]
        next_hop = entry[2]
        return (prefix, next_hop)

    bgp_table_entries = list(map(convert_entry_to_prefix_nexthop_pair, bgp_table_entries))

    return bgp_table_entries

def main():
    bgp_table_file_path = "bgptable.txt"
    bgp_table_entries = parse_bgp_table_file(bgp_table_file_path)

    # printing the first 10 entries (TODO: delete)
    for i in range(9):
        print(bgp_table_entries[i])

if __name__ == "__main__":
    main()