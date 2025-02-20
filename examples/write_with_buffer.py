#!/usr/bin/env python3
#
# This example illustrates how to write miniSEED using a rolling
# buffer of potentially multi-channel data.   This pattern of usage is
# particularly useful for applications that need to generate miniSEED
# in a continuous stream for an unknown (long) duration.  Another use
# would be to avoid large volumes of data in memory by incrementally
# generating miniSEED.
#
# In this example, a sine wave generator is used to create synthetic
# data for 3 channels by producing 100 samples at a time.
#
# The general pattern is:
#
#   def record_handler() # A function that is called when records are generated
#
#   mstl = MSTraceList() # Create an empty MSTraceList object
#
#   Loop on input data:
#     mstl.add_data()    # Add data to the MSTraceList object
#     mstl.pack(flush_data=False) # Generate records and call record_handler() for each
#
#   mstl.pack(flush_data=True) # Flush any data remaining in the buffers
#
#
# This file is part of the the Python mseedlib package.
# Copywrite (c) 2024, EarthScope Data Services

import math
from mseedlib import MSTraceList, timestr2nstime, sampletime

output_file = "output.mseed"


def sine_generator(start_degree=0, yield_count=100, total=1000):
    """A generator returning a continuing sequence for a sine values."""
    generated = 0
    while generated < total:
        bite_size = min(yield_count, total - generated)

        # Yield a tuple of 3 lists of continuing sine values
        yield list(
            map(
                lambda x: int(math.sin(math.radians(x)) * 500),
                range(start_degree, start_degree + bite_size),
            )
        )

        start_degree += bite_size
        generated += bite_size


# Define 3 generators with offset starting degrees
generate_yield_count = 100
sine0 = sine_generator(start_degree=0, yield_count=generate_yield_count)
sine1 = sine_generator(start_degree=45, yield_count=generate_yield_count)
sine2 = sine_generator(start_degree=90, yield_count=generate_yield_count)


def record_handler(buffer, handlerdata):
    """Write buffer to the file handle in handler data.

    This callback function can be changed to do anything you want
    with the generated records.  For example, you could write them
    to a file, to a pipe, or send them over a network connection.
    """
    handlerdata["fh"].write(buffer)


file_handle = open(output_file, "wb")

mstl = MSTraceList()

total_samples = 0
total_records = 0
sample_rate = 40.0
start_time = timestr2nstime("2024-01-01T15:13:55.123456789Z")
format_version = 2
record_length = 512

# A loop that iterativately adds data to traces in the list.
#
# This could be any data collection operation that continually
# adds samples to the trace list.
for i in range(10):

    # Add new synthetic data to each trace using generators
    mstl.add_data(
        sourceid="FDSN:XX_TEST__B_S_0",
        data_samples=next(sine0),
        sample_type="i",
        sample_rate=sample_rate,
        start_time=start_time,
    )

    mstl.add_data(
        sourceid="FDSN:XX_TEST__B_S_1",
        data_samples=next(sine1),
        sample_type="i",
        sample_rate=sample_rate,
        start_time=start_time,
    )

    mstl.add_data(
        sourceid="FDSN:XX_TEST__B_S_2",
        data_samples=next(sine2),
        sample_type="i",
        sample_rate=sample_rate,
        start_time=start_time,
    )

    # Update the start time for the next iteration of synthetic data
    start_time = sampletime(start_time, generate_yield_count, sample_rate)

    # Generate full records and do not flush the data biffers
    (packed_samples, packed_records) = mstl.pack(
        record_handler,
        handlerdata={"fh": file_handle},
        format_version=format_version,
        record_length=record_length,
        flush_data=False,
    )

    total_samples += packed_samples
    total_records += packed_records

# Flush the data buffers and write any data to records
(packed_samples, packed_records) = mstl.pack(
    record_handler,
    handlerdata={"fh": file_handle},
    format_version=format_version,
    record_length=record_length,
    flush_data=True,
)

total_samples += packed_samples
total_records += packed_records

file_handle.close()

print(f"Packed {total_samples} samples in {total_records} records")
