#!/usr/bin/env python3
#
# Read miniSEED file(s) from a stream (stdin), select those that
# fall within the selected earliest and latest times, and write out
# to a stream (stdout).  Records that contain the selected times are
# trimmed to the selected times.
#
# Example usage:
#  cat input.mseed | stream_timewindow.py -e 2023-01-01T00:00:00 -l 2023-01-02T00:00:00 > output.mseed
#
# This file is part of the Python mseedlib module.
# Copywrite (c) 2024, EarthScope Data Services

import sys
import argparse
from mseedlib import MS3RecordReader, MS3RecordBufferReader, timestr2nstime

# A global record buffer for repacked records
record_buffer = b''


def process_stream(args):
    records_written = 0
    bytes_written = 0

    print("Reading miniSEED from stdin, writing to stdout", file=sys.stderr)

    # Read miniSEED from stdin
    with MS3RecordReader(sys.stdin.fileno()) as msreader:
        for msr in msreader:

            # Skip records before earliest selection time
            if args.earliest and msr.endtime < args.earliest:
                continue

            # Skip records after latest selection time
            if args.latest and msr.starttime > args.latest:
                continue

            repacked_record = None

            # Trim record to selection time range if it contains selection times
            if ((args.earliest and msr.starttime < args.earliest <= msr.endtime) or
                    (args.latest and msr.starttime <= args.latest < msr.endtime)):
                repacked_record = trim_record(msr, args.earliest, args.latest)

            # Write either repacked or orignal record to stdout
            sys.stdout.buffer.write(repacked_record if repacked_record else msr.record)

            records_written += 1
            bytes_written += msr.reclen

    print(f"Wrote {records_written} records, {bytes_written} bytes", file=sys.stderr)


def record_handler(record, handler_data):
    '''A callback function for MS3Record.set_record_handler()'''
    global record_buffer
    record_buffer = bytes(record)


def trim_record(msr, earliest, latest):
    '''Trim a miniSEED record to the specified start and end times'''

    # Cannot trim time coverage of a record with no coverage
    if msr.samplecnt == 0 and msr.samprate == 0.0:
        return

    # Re-parse the record and decode the data samples
    buffer = bytearray(msr.record)  # Mutable/writable buffer required
    with MS3RecordBufferReader(buffer, unpack_data=True) as msreader:
        msr = msreader.read()

        starttime = msr.starttime
        endtime = msr.endtime
        sample_period_ns = int(1e9 / msr.samprate)
        datasamples = msr.datasamples[:]

        # Trim early samples to the earliest time
        if earliest and starttime < earliest <= endtime:
            count = 0
            while starttime < earliest:
                starttime += sample_period_ns
                count += 1

            msr.starttime = starttime
            datasamples = datasamples[count:]

        # Trim late samples to the latest time
        if latest and starttime <= latest < endtime:
            count = 0
            while endtime > latest:
                endtime -= sample_period_ns
                count += 1

            datasamples = datasamples[:-count]

        # Pack miniSEED record with handler writing to global record_buffer
        msr.pack(record_handler, datasamples=datasamples, sampletype=msr.sampletype)

        return record_buffer


def parse_timestr(timestr):
    '''Helper for argparse to convert a time string to a nanosecond time value'''
    try:
        return timestr2nstime(timestr)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid time string: {timestr}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Streaming modifications of miniSEED')
    parser.add_argument('--earliest', '-e', type=parse_timestr,
                        help='Specify the earliest time to output')
    parser.add_argument('--latest', '-l', type=parse_timestr,
                        help='Specify the latest time to output')

    args = parser.parse_args()

    if args.earliest and args.latest and args.earliest > args.latest:
        parser.error("Earliest time is after latest time")

    process_stream(args)
