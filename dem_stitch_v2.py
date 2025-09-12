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
    tmp_overlap_diff = f"tmp_overlap_diff_{postfix}"
    tmp_result = f"tmp_result_{postfix}"
    tmp_a_shifted = f"tmp_a_shifted_{postfix}"
    tmp_diff_A = f"tmp_diff_A{postfix}"
    tmp_postshift_diff = f"tmp_postshift_diff_{postfix}"
    
    TMP.append(tmp_postshift_diff)    
    TMP.extend([tmp_diff_A, tmp_a_shifted])
    TMP.extend([overlap_mask, tmp_median_map, tmp_result])

    # Step 1: Identify overlapping area
    gscript.mapcalc(f"{overlap_mask} = if(!isnull({input_A}) && !isnull({input_B}), 1, null())", overwrite=True)

    # Step 2: Compute median in overlapping area
    gscript.mapcalc(
    f"{tmp_overlap_diff} = if(!isnull({input_A}) && !isnull({input_B}) && "
    f"{input_A} <= 50 && {input_B} <= 50, "
    f"{input_A} - {input_B}, null())",
    overwrite=True
    )
    
    # Finding the median of the overlapping difference
    stats = gscript.parse_command('r.univar', map=tmp_overlap_diff, flags='ge') #add a ge flag for extended statistics like median
    median_val = float(stats['median'])
    
    gscript.mapcalc(
    f'"{tmp_a_shifted}" = "{input_A}" - {median_val}',
    overwrite=True
    )
    
    # Findng the overlapping difference between the shifted a and b 
    gscript.mapcalc(
    f"{tmp_postshift_diff} = if(!isnull({tmp_a_shifted}) && !isnull({input_B}), "
    f"{tmp_a_shifted} - {input_B}, null())",
    overwrite=True
    )
    
    # Final step: Stitch together: median in overlap, else input_A or input_B
    gscript.mapcalc(
    f"{tmp_result} = if(!isnull({input_A}), {tmp_a_shifted}, {input_B})",
    overwrite=True
    )
    
    # Finding the standard deviation of the overlapping difference
    stats = gscript.parse_command('r.univar', map=tmp_postshift_diff, flags='ge') #add a ge flag for extended statistics like median
    sd_val = float(stats['stddev'])
    
    print(f"Standard deviation of overlapping difference: {sd_val}")

    # Copy result to output
    gscript.run_command('g.copy', raster=f"{tmp_result},{output}", overwrite=True)

if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())


