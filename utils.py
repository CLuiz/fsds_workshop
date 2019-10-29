
def read_config(config_file):
    # read file ansd split on newlines
    with open(config_file, 'r') as f:
        val_list = f.readlines()
    # split on = sign
    split_vals = [x.split('=') for x in val_list]
    # return dict of values. Check length to prevent error on malformed entries
    return {item[0]: item[1] for item in split_vals if len(item) == 2}
