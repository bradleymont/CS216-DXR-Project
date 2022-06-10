from create_dxr_tables import create_dxr_tables
import json

def convert_dot_notation_to_16_bit_hex(dot_notation):
    upper_byte_str, lower_byte_str = dot_notation.split(".")

    upper_byte_int = int(upper_byte_str)
    lower_byte_int = int(lower_byte_str)

    upper_byte_hex = hex(upper_byte_int)[2:]
    lower_byte_hex = hex(lower_byte_int)[2:]

    if len(upper_byte_hex) == 1:
        upper_byte_hex = "0" + upper_byte_hex

    if len(lower_byte_hex) == 1:
        lower_byte_hex = "0" + lower_byte_hex

    return upper_byte_hex + lower_byte_hex

def add_lookup_table_to_table_entries(lookup_table, table_entries):
    for msb_in_dot_notation, val in lookup_table.items():
        msb_in_hex = convert_dot_notation_to_16_bit_hex(msb_in_dot_notation)

        table_entry = {
            "table": "MyIngress.L1",
            "match": { "meta.ip_H": msb_in_hex },
            "action_name": "MyIngress.L1_respond",
            "action_params": { "ans": val }
        }

        table_entries.append(table_entry)        

def add_range_table_to_table_entries(range_table, table_entries):
    for i, val in enumerate(range_table):

        table_entry = {
            "table": "MyIngress.L2",
            "match": { "m": i },
            "action_name": "MyIngress.L2_respond",
            "action_params": { "ans": val }
        }

        table_entries.append(table_entry)

def add_next_hop_table_to_table_entries(next_hop_to_offset, table_entries):
    del next_hop_to_offset["DROP"]
    for next_hop, offset in next_hop_to_offset.items():
        table_entry = {
            "table": "MyEgress.L3",
            "match": { "meta.ip_L": offset },
            "action_name": "MyEgress.L3_respond",
            "action_params": { "ans": next_hop }
        }
    
        table_entries.append(table_entry)

def main():
    lookup_table, range_table, next_hop_to_offset = create_dxr_tables()

    table_entries = []

    add_lookup_table_to_table_entries(lookup_table, table_entries)

    add_range_table_to_table_entries(range_table, table_entries)

    add_next_hop_table_to_table_entries(next_hop_to_offset, table_entries)

    res = {
        "target": "bmv2",
        "p4info": "build/basic.p4.p4info.txt",
        "bmv2_json": "build/basic.json",
        "table_entries": table_entries
    }

    f = open("OUTPUT.json", "w")
    f.write(json.dumps(res, indent=4))
    f.close()

if __name__ == "__main__":
    main()