#!/usr/bin/env python3
#
# Read miniSEED file(s) using the mseedlib module and decode
# data samples directly into NumPy arrays.
#
# The data are organized into a list of dictionaries, one for
# each contiguous trace of data.  The dictionaries contain very
# basic metadata and a NumPy array of data samples.  This data
# structure is for illustration only, and would like need
# adaptation for a real application.
#
# This file is part of the mseedlib module.
# Copywrite (c) 2024, EarthScope Data Services

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

mstl = MSTraceList()

# Read all input files, creating a record lists and _not_ unpacking data samples
for file in input_files:
    print("Reading file: %s" % file)
    mstl.read_file(file, unpack_data=False, record_list=True)

for traceid in mstl.traceids():
    for segment in traceid.segments():
        # Fetch estimated sample size and type
        (sample_size, sample_type) = segment.sample_size_type

        dtype = nptype[sample_type]

        # Allocate NumPy array for data samples
        data_samples = np.zeros(segment.samplecnt, dtype=dtype)

        # Unpack data samples into allocated NumPy array
        segment.unpack_recordlist(buffer_pointer=np.ctypeslib.as_ctypes(data_samples),
                                  buffer_bytes=data_samples.nbytes)

        # Create a dictionary for the trace with basic metadata
        trace = {'sourceid': traceid.sourceid,
                 'NSLC': sourceid2nslc(traceid.sourceid),
                 'publication_version': traceid.pubversion,
                 'start_time': segment.starttime_str(),
                 'end_time': segment.endtime_str(),
                 'sample_rate': segment.samprate,
                 'data_samples': data_samples}

        traces.append(trace)

print(traces)