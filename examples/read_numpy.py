#!/usr/bin/env python3
#
# Read miniSEED file(s) using the mseedlib module and decode
# data samples directly into NumPy arrays.
#
# The data are organized into a list of dictionaries, one for
# contiguous trace of data.  The dictionaries contain very
# basic metadata and a NumPy array of data samples.

import os
import sys
import numpy as np
from mseedlib import MSTraceList, sourceid2nslc

input_files = []

# Verify that input files are readable
for arg in sys.argv[1:]:
    if os.access(arg, os.R_OK):
        input_files.append(arg)
    else:
        sys.exit("Cannot read file: %s" % arg)

if not input_files:
    sys.exit("No input files specified")

# List of dictionaries for each trace
traces = []

# Translate libmseed sample type to numpy type
nptype = {'i': np.int32, 'f': np.float32, 'd': np.float64, 't': np.char}

# Parse input data into a trace list, creating record lists for each trace
mstl = MSTraceList()

# Read all input files
for file in input_files:
    print("Reading file: %s" % file)
    mstl.readFile(file, unpack_data=False, record_list=True)

for traceid in mstl.traceids():
    for segment in traceid.segments():

        # Create a dictionary for the trace with basic metadata
        trace = {'sourceid': traceid.sourceid,
                 'NSLC': sourceid2nslc(traceid.sourceid),
                 'publication_version': traceid.pubversion,
                 'start_time': segment.starttime_str(),
                 'end_time': segment.endtime_str(),
                 'sample_rate': segment.samprate}

        # Fetch estimated sample size and type
        (sample_size, sample_type) = segment.sample_size_type

        dtype = nptype[sample_type]

        # Allocate NumPy array for data samples
        data_samples = np.zeros(segment.samplecnt, dtype=dtype)

        # Unpack data samples into allocated NumPy array
        segment.unpack_recordlist(buffer_pointer=np.ctypeslib.as_ctypes(data_samples),
                                  buffer_bytes=data_samples.nbytes)

        # Add data samples to trace dictionary
        trace['data_samples'] = data_samples

        traces.append(trace)

print(traces)