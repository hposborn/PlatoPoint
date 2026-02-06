# PlatoPoint

This is an extremely simplified function which will allow you to check if a given target is likely to be observed by PLATO. It is only built on public information (LOPS2 field position, camera FoVs/offsets, gap width, etc), and basic speherical geometry assumptions (which may not hold given the complexities of lenses). The simplifying assumptions (e.g. a 18arcmin width) may not be correct on flight. Hence this tool should not be used to ensure if a target truly is PLATO visible for observations, but could be used to get a rough idea of the visibility as we are many months before launch.

For the real tools, please consult the official PLATO consortium visibility tool (which, as of Feb 2026, is not yet released), the PLATO Guest Observer feasibility processer (CfP) which is also not yet released. Additionally there is functionality in (PlatoSim)[https://ivs-kuleuven.github.io/PlatoSim3] which may be used to do a more thorough job of these calculations, but it is not so user friendly.

### Use

```
from PlatoPoint import PlatoPoint

viztool= PlatoPoint()

ras=np.array([60,100,125])
decs=np.array(-42,-48,-52])

ncams=viztool(ras,decs)
```

### Installation

Prerequisites: `python 3.8+, numpy, astropy, pandas`
`git clone https://github.com/hposborn/platopoint`
`cd platopoint`
And then run `pip install .` or `python setup.py --install`

### Command Line Usage

You can run PlatoPoint directly from the terminal to check targets or generate statistics.
1. Check a Single Target

Determine how many cameras (0-4) are observing a specific sky coordinate.

`python PlatoPoint.py --ra 90.0 --dec -45.0`

Target coordinates: RA 90.0, Dec -45.0
Number of observing cameras: 4
Status: OBSERVED

2. Batch Processing (CSV)

Process a list of targets from a CSV file. The file must contain columns named ra and dec (case-insensitive).

`python PlatoPoint.py --file my_targets.csv`

Output:
    Generates a new file: plato_coverage_output.csv
    Adds a column n_cameras containing the camera count (0-4) for each star.

### Python Library Usage

You can import PlatoPoint into your own scripts to perform calculations programmatically.
Python

```
from PlatoPoint import PlatoPoint

# 1. Initialize the Payload Model
# This sets up the coordinate frames and camera geometry
plato = PlatoPoint()

# 2. Check a single coordinate (ICRS)
ra, dec = 250.5, -20.0
n_cams = plato.check_observation(ra, dec)
print(f"Star is seen by {int(n_cams)} cameras.")

# 3. Check an array of coordinates (Vectorized)
import numpy as np
ras = np.array([100.0, 101.0, 102.0])
decs = np.array([-45.0, -45.0, -45.0])

counts = plato.check_observation(ras, decs)
# Returns numpy array: [4, 4, 3]

# 4. Calculate total area statistics
stats = plato.calculate_coverage_breakdown(num_samples=100_000)
print(f"Total FOV: {stats['Total']:.2f} deg²")
```
