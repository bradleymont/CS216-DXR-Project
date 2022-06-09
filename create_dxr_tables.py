from build_search_data_structure import build_search_data_structure

# TODO: build the tables

def main():
    interval_to_next_hop = build_search_data_structure()

    # print first 10 entries of data structure
    i = 0
    for key in interval_to_next_hop:
        if i == 10: break
        print(key, interval_to_next_hop[key])
        i += 1

    print(str(len(interval_to_next_hop)) + " range entries")

if __name__ == "__main__":
    main()