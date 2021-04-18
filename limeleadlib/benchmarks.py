import os
import re
import json
import yaml
import argparse

import pandas

_SPLIT_ON_X = re.compile(r'&#215;')

ISA_NAMEMAP = {
    "parisc": "PA-RISC",
    "x86": "x86"
}

def flatten_results(records):
    """Flattens nested list of benchmark records into a list of flat records

    Args:
        records (list): List of dictionaries, optionally containing the
            'results' key which contains a list of key-value pairs to combine
            with the parent keys/values to generate flat records.

    Returns:
        list: List of dictionaries suitable to be passed to
        pandas.DataFrame.from_dict().
    """
    flattened = []
    for record in records:
        if 'results' in record:
            for result in record['results']:
                tmp_record = record.copy()
                del tmp_record['results']
                tmp_record.update(result)
                flattened.append(tmp_record)
        else:
            flattened.append(record)
    return flattened

def rekey_row(row, brief=False):
    if '&#215' in row['clock']:
        cores, clock = map(int, _SPLIT_ON_X.split(row['clock']))
    else:
        cores = 1
        clock = int(row['clock'])
    if clock < 1000:
        clock = "{:d} MHz".format(clock)
    else:
        clock = "{:.1f} GHz".format(clock / 1000)
    if brief:
        return "{} ({}){}".format(
            row['processor'],
            clock,
            " {:d} cores".format(cores) if cores > 1 else "")
    else:
        return "{} ({}) {:d} core{}".format(
            row['processor'],
            clock,
            cores, "s" if cores != 1 else "")

def load_datasets(datafiles):
    all_results = None

    for datafile in datafiles:
        from_dict = yaml.load(open(datafile, 'r'), Loader=yaml.SafeLoader)
        results_df = pandas.DataFrame.from_dict(flatten_results(from_dict))
        results_df['isa'] = datafile.split(os.sep)[-1].split('_', 1)[0]
        if all_results is None:
            all_results = results_df
        else:
            all_results = pandas.concat((all_results, results_df))

    return all_results

def generate_plotly_dataset(dataframe, key='wall_secs'):
    dataframe['index'] = dataframe.apply(lambda x: rekey_row(x, brief=True), axis=1)
    dataframe= dataframe.set_index('index')
    sorted_df = dataframe[dataframe[key].notna()].sort_values(by=key, ascending=True)

    dataset = []
    for isa in sorted_df['isa'].unique():
        filt = sorted_df['isa'] == isa
        dataset.append({
            'y': list(sorted_df[filt][key].index.values),
            'x': [int(x) for x in sorted_df[filt][key]],
            'name': ISA_NAMEMAP.get(isa, isa.upper()),
            'type': 'bar',
            'orientation': 'h',
            'marker': {
                'line': {
                    'color': '#000000',
                    'width': 1
                }
            }
        })
    return dataset

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('datafiles', nargs='+', type=str, help="One or more json/yaml files containing benchmark results")
    parser.add_argument("-k", "--key", type=str, default="wall_secs", help="benchmark metric to plot (default: wall_secs)")
    parser.add_argument("-o", "--output", type=str, default=None, help="file name to save output (default: use stdout)")
    args = parser.parse_args(argv)
    dataset = generate_plotly_dataset(
        load_datasets(datafiles=args.datafiles),
        key=args.key)
    if args.output:
        json.dump(dataset, open(args.output, 'w'))
    else:
        print(json.dumps(dataset))

if __name__ == "__main__":
    main()
