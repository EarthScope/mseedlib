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

TODO

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

Copyright (C) 2023 Chad Trabant, EarthScope Data Services
