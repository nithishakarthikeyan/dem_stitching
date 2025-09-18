**DEM Stitching**

Basal channel analysis often requires continuous elevation data but DEM tiles usually have uneven elevation values along their edges. This leads to mismatches that can affect accuracy.

This code is written as a GRASS GIS extension using gscript. It automates the process of stitching two DEM tiles into a single seamless surface, correcting inconsistencies and ensuring smoother elevation transitions. The result is a cleaner DEM mosaic that supports more reliable basal channel detection and downstream analysis.

**How to run this code**
1. In the Grass Terminal:
grass /path/to/grassdata/folder --exec /path/to/dem_stitching2.py \
  input_a= DEM_file_A\
  input_b= DEM_file_B\
  output= output_file_name
