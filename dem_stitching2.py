#!/usr/bin/env python

#%module
#% description: Smoothly blends two DEMs by shifting one DEM to match the median of the other.
#% keyword: raster
#% keyword: patch
#%end

#%option
#% key: input_a
#% type: string
#% gisprompt: old,cell,raster
#% description: Name of first input DEM
#% required: yes
#%end

#%option
#% key: input_base
#% type: string
#% gisprompt: old,cell,raster
#% description: Name of second input DEM (base)
#% required: yes
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: Output smoothed raster map
#% required: yes
#%end

import os
import sys
import atexit
import grass.script as gscript

TMP = []

def cleanup():
    if TMP:
        gscript.run_command('g.remove', flags='f', type=['raster'], name=TMP, quiet=True)

def main():
    input_A = options['input_a']
    input_base = options['input_base']
    output = options['output']

    postfix = str(os.getpid())
    shifted_a = f"shifted_a_{postfix}"
    stitched_result = f"stitched_result_{postfix}"

    TMP.extend([shifted_a, stitched_result])

    # --- Step 1: Get median of both maps ---
    stats_a = gscript.parse_command('r.univar', map=input_A, flags='ge')
    stats_base = gscript.parse_command('r.univar', map=input_base, flags='ge')

    median_a = float(stats_a['median'])
    median_base = float(stats_base['median'])

    # --- Step 2: Compute shift and apply it to A ---
    shift = median_base - median_a
    gscript.mapcalc(f"{shifted_a} = {input_A} + {shift}", overwrite=True)

    # --- Step 3: Stitch the two DEMs ---
    # Use shifted A where it exists; otherwise use base
    gscript.mapcalc(
        f"{stitched_result} = if(!isnull({shifted_a}), {shifted_a}, {input_base})",
        overwrite=True
    )

    # --- Step 4: Copy final result to output ---
    gscript.run_command('g.copy', raster=f"{stitched_result},{output}", overwrite=True)

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())
