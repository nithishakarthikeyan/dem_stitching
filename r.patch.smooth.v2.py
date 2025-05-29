#!/usr/bin/env python

#%module
#% description: Smoothly blends two DEMs with optional overlap handling.
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
#% key: input_b
#% type: string
#% gisprompt: old,cell,raster
#% description: Name of second input DEM
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
        gscript.run_command('g.remove', flags='f', type=['raster', 'vector'], name=TMP, quiet=True)

def main():
    input_A = options['input_a']
    input_B = options['input_b']
    output = options['output']

    postfix = str(os.getpid())
    overlap_mask = f"tmp_overlap_mask_{postfix}"
    tmp_median_map = f"tmp_median_map_{postfix}"
    tmp_result = f"tmp_result_{postfix}"
    tmp_a_shifted = f"tmp_a_shifted_{postfix}"
    tmp_b_shifted = f"tmp_b_shifted_{postfix}"
    tmp_diff_A = f"tmp_diff_A{postfix}"
    tmp_diff_B = f"tmp_diff_B{postfix}"

    TMP.extend([tmp_diff_A, tmp_a_shifted])
    TMP.extend([tmp_diff_B, tmp_b_shifted])
    TMP.extend([overlap_mask, tmp_median_map, tmp_result])

    # Step 1: Identify overlapping area
    gscript.mapcalc(f"{overlap_mask} = if(!isnull({input_A}) && !isnull({input_B}), 1, null())", overwrite=True)

    # Step 2: Compute median (mean) in overlapping area
    gscript.mapcalc(
        f"{tmp_median_map} = if(!isnull({input_A}) && !isnull({input_B}), "
        f"({input_A} + {input_B}) / 2, null())",
        overwrite=True
    )
    
    # Step 3: Compute difference between mean elevation of A and median of overlap
    gscript.mapcalc(f"""
    {tmp_diff_A} = if(!isnull({input_A}) && !isnull({input_B}),
                    ({tmp_median_map} - {input_A}),
                    null())
    """, overwrite=True)
    
    # Calculate the mean overall difference
    stats = gscript.parse_command('r.univar', map=tmp_diff_A, flags='g')
    mean_diff = float(stats['mean'])
    
    # Shift all of input_A by the mean difference
    gscript.mapcalc(f"""
    {tmp_a_shifted} = {input_A} + {mean_diff}
     """, overwrite=True)
    
    # Do the same for DEM B
    gscript.mapcalc(f"""
    {tmp_diff_B} = if(!isnull({input_A}) && !isnull({input_B}),
                    ({tmp_median_map} - {input_B}),
                    null())
    """, overwrite=True)
    
    # Calculate the mean overall difference
    stats = gscript.parse_command('r.univar', map=tmp_diff_B, flags='g')
    mean_diff = float(stats['mean'])
    
    # Shift all of input_B by the mean difference
    gscript.mapcalc(f"""
    {tmp_a_shifted} = {input_B} + {mean_diff}
     """, overwrite=True)
    

    # Final step: Stitch together: median in overlap, else input_A or input_B
    gscript.mapcalc(
        f"{tmp_result} = if(!isnull({input_A}) && !isnull({input_B}), "
        f"{tmp_median_map}, if(!isnull({input_A}), {input_A}, {input_B}))",
        overwrite=True
    )

    # Copy result to output
    gscript.run_command('g.copy', raster=f"{tmp_result},{output}", overwrite=True)

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())
