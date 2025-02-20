#!/usr/bin/env python3
#
# Read miniSEED file(s) from a stream, accumulate stats, and write to
# a stream.  For this illustration input is stdin, output is stdout, and
# stats are printed to stderr on completion.
#
# This file is part of the Python mseedlib module.
# Copywrite (c) 2024, EarthScope Data Services

import sys
import pprint
from collections import defaultdict
from mseedlib import MS3RecordReader, nstime2timestr

# Container for trace stats
trace_stats = {}

print("Reading miniSEED from stdin, writing to stdout", file=sys.stderr)

# Read miniSEED from stdin
with MS3RecordReader(sys.stdin.fileno()) as msreader:
    for msr in msreader:

        stats = trace_stats.setdefault(msr.sourceid, defaultdict(int))

        stats["record_count"] += 1
        stats["sample_count"] += msr.samplecnt
        stats["bytes"] += msr.reclen

        # Track publication versions
        if msr.pubversion not in stats.setdefault("pubversions", []):
            stats["pubversions"].append(msr.pubversion)

        # Track format versions
        if msr.formatversion not in stats.setdefault("formatversions", []):
            stats["formatversions"].append(msr.formatversion)

        # Track earliest sample time
        if "earliest" not in stats or msr.starttime > stats["earliest"]:
            stats["earliest"] = msr.starttime

        # Track latest sample time
        if "latest" not in stats or msr.endtime > stats["latest"]:
            stats["latest"] = msr.endtime

        # Write raw miniSEED record to stdout
        sys.stdout.buffer.write(msr.record)

# Traverse trace stats and add date-time string values for earliest and latest
for stats in trace_stats.values():
    stats["earliest_str"] = nstime2timestr(stats["earliest"])
    stats["latest_str"] = nstime2timestr(stats["latest"])

# Pretty print stats to stderr (to avoid mixing with stdout)
pp = pprint.PrettyPrinter(stream=sys.stderr, indent=4, sort_dicts=False)
pp.pprint(trace_stats)
