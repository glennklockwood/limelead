import argparse
import json
import os
import re
import math
import yaml

_SPLIT_ON_X = re.compile(r'\s*&#215;\s*')

ISA_NAMEMAP = {
    "parisc": "PA-RISC",
    "x86": "x86"
}

TABLE_COLUMNS = (
    "model",
    "processor",
    "cores_and_clock",
    "wall_secs",
    "memreorder_secs",
)

def _is_missing(value):
    if value is None or value == "":
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False

def _reduce_mhz(clock):
    if clock < 1000:
        return "{:d} MHz".format(clock)
    return "{:.1f} GHz".format(clock / 1000)

def _flatten_results(records):
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

def flatten_results(records):
    return _flatten_results(records)

def _fix_clock_vals(record):
    if 'clock' in record and isinstance(record['clock'], str):
        if '&#215;' in record['clock']:
            cores, clock = map(int, _SPLIT_ON_X.split(record['clock']))
        else:
            cores, clock = 1, int(record['clock'])
    else:
        clock = int(record['clock_mhz'])
        if 'cores_used' in record and not _is_missing(record['cores_used']):
            cores = int(record['cores_used'])
        else:
            cores = 1
    return cores, clock

def _normalize_record(record):
    cores, clock = _fix_clock_vals(record)
    record = record.copy()
    record['cores_used'] = cores
    record['clock_mhz'] = clock
    record['cores_and_clock'] = "{:d} &#215; {}".format(
        cores,
        _reduce_mhz(clock))
    return record

def _load_records(datafiles):
    all_records = []
    for datafile in datafiles:
        with open(datafile, 'r') as handle:
            records = yaml.load(handle, Loader=yaml.SafeLoader)
        isa = os.path.basename(datafile).split('_', 1)[0]
        for record in _flatten_results(records):
            normalized = _normalize_record(record)
            normalized['isa'] = isa
            all_records.append(normalized)
    return all_records

def load_datasets(datafiles):
    return _load_records(datafiles)

def _rekey_row(record, brief=False):
    cores = record['cores_used']
    if brief:
        return "{} ({}){}".format(
            record['processor'],
            _reduce_mhz(record['clock_mhz']),
            " {:d} cores".format(cores) if cores > 1 else "")
    return "{} ({}) {:d} core{}".format(
        record['processor'],
        _reduce_mhz(record['clock_mhz']),
        cores, "s" if cores != 1 else "")

def rekey_row(record, brief=False):
    return _rekey_row(record, brief=brief)

def _as_int(value):
    if _is_missing(value):
        return None
    return int(value)

def generate_plotly_dataset(records, key='wall_secs'):
    dataset = []
    by_isa = {}
    for record in records:
        by_isa.setdefault(record['isa'], []).append(record)

    for isa, rows in by_isa.items():
        filtered = [r for r in rows if not _is_missing(r.get(key))]
        sorted_rows = sorted(filtered, key=lambda r: _as_int(r.get(key)))
        dataset.append({
            'y': [_rekey_row(r, brief=True) for r in sorted_rows],
            'x': [_as_int(r.get(key)) for r in sorted_rows],
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

def generate_table_payload(records):
    payload = {}
    for record in records:
        isa = record['isa']
        row = {}
        for key in TABLE_COLUMNS:
            value = record.get(key)
            if key in ("wall_secs", "memreorder_secs"):
                value = _as_int(value)
            row[key] = value
        payload.setdefault(isa, []).append(row)
    return payload

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('datafiles', nargs='+', type=str)
    parser.add_argument("-m", "--mode", type=str, choices=("plot", "tables"), required=True)
    parser.add_argument("-k", "--key", type=str, default="wall_secs")
    parser.add_argument("-o", "--output", type=str, default=None)
    args = parser.parse_args(argv)

    records = _load_records(args.datafiles)
    if args.mode == "plot":
        data = generate_plotly_dataset(records, key=args.key)
    else:
        data = generate_table_payload(records)

    if args.output:
        with open(args.output, 'w') as handle:
            json.dump(data, handle)
    else:
        print(json.dumps(data))

if __name__ == "__main__":
    main()
