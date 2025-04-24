import pytest
import math


# A sine wave of 500 samples
sine_500 = list(map(lambda x: int(math.sin(math.radians(x)) * 500), range(0, 500)))
