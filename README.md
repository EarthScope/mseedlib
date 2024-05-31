# mseedlib - a Python package to read and write miniSEED formatted data

The mseedlib package allows for reading and writing of [miniSEED](https://docs.fdsn.org/projects/miniseed3)
formatted data, which is commonly used for seismological and other geophysical
time series data.

The module leverages the C-language [libmseed](https://earthscope.github.io/libmseed)
for most of the heavy data format and manipulation work.

## Installation

The [releases](https://pypi.org/project/mseedlib/) should be installed
directly from PyPI with, for example, `pip install mseedlib`.
The package does not depend on anything other than the Python standard library.

## Example usage

Working programs for a variety of use cases ca be found in the
[examples](https://github.com/EarthScope/mseedlib/tree/main/examples) directory of the repository.

Read a file and print details from each record:
```Python
from mseedlib import MS3RecordReader,TimeFormat

with MS3RecordReader('testdata-3channel-signal.mseed3') as msreader:
    for msr in msreader:
        # Print values directly
        print(f'   SourceID: {msr.sourceid}, record length {msr.reclen}')
        print(f' Start Time: {msr.starttime_str(timeformat=TimeFormat.ISOMONTHDAY_SPACE_Z)}')
        print(f'    Samples: {msr.samplecnt}')

        # Alternatively, use the library print function
        msr.print()
```

Read a file into a trace list and print the list:
```Python
from mseedlib import MSTraceList

mstl = MSTraceList('testdata-3channel-signal.mseed3')

# Print the trace list using the library print function
mstl.print(details=1, gaps=True)

# Alternatively, traverse the data structures and print each trace ID and segment
for traceid in mstl.traceids():
    print(traceid)

    for segment in traceid.segments():
        print('  ', segment)
```

Writing miniSEED requires specifying a "record handler" function that is
a callback to consume, and do whatever you want, with generated records.

Simple example of writing multiple channels of data:
```Python
import math
from mseedlib import MSTraceList, timestr2nstime

# Generate synthetic sinusoid data, starting at 0, 45, and 90 degrees
data0 = list(map(lambda x: int(math.sin(math.radians(x)) * 500), range(0, 500)))
data1 = list(map(lambda x: int(math.sin(math.radians(x)) * 500), range(45, 500 + 45)))
data2 = list(map(lambda x: int(math.sin(math.radians(x)) * 500), range(90, 500 + 90)))

mstl = MSTraceList()

sample_rate = 40.0
start_time = timestr2nstime("2024-01-01T15:13:55.123456789Z")
format_version = 2
record_length = 512

# Add synthetic data to the trace list
mstl.add_data(sourceid="FDSN:XX_TEST__B_S_0",
              data_samples=data0, sample_type='i',
              sample_rate=sample_rate, start_time=start_time)

mstl.add_data(sourceid="FDSN:XX_TEST__B_S_0",
              data_samples=data1, sample_type='i',
              sample_rate=sample_rate, start_time=start_time)

mstl.add_data(sourceid="FDSN:XX_TEST__B_S_0",
              data_samples=data2, sample_type='i',
              sample_rate=sample_rate, start_time=start_time)

# Record handler called for each generated record
def record_handler(record, handler_data):
    handler_data['fh'].write(record)

file_handle = open('output.mseed', 'wb')

# Generate miniSEED records
mstl.pack(record_handler,
          {'fh':file_handle},
          flush_data=True)
```

## Package design rationale

The package functionality and exposed API are designed to support the most
common use cases of reading and writing miniSEED data using `libmseed`.
Extensions of data handling beyond the functionality of the library are
out-of-scope for this package.  Furthermore, the naming of functions,
classes, arguments, etc. follows the naming used in the library in order
to reference their fundamentals at the C level if needed; even though this
leaves some names distinctly non-Pythonic.

In a nutshell, the goal of this package is to provide just enough of a Python
layer to `libmseed` to handle the most common cases of miniSEED data without
needing to know any of the C-level details.

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Copyright (C) 2024 Chad Trabant, EarthScope Data Services
