import pandas as pd
import geopandas as gpd

import sys
sys.path.append('path_to_repo')

import mmh_spatial

## Input Files
parcel = gpd.read_file('DenverParcels/')

## get_osm_footprints is a convenience wrapper for OSMNX to download building footprints from OSM
## alternatively you can specify a file containing building footprints
foot = mmh_spatial.get_osm_footprints(parcel, save = 'footprints')

## Run simplify_* helper functions to add necessary fields
sf = mmh_spatial.simplify_footprints(foot, method = 'None', reproject = True)
sp = mmh_spatial.simplify_parcel(parcel, reproject = True, method = 'simple')

## run make_geometries to add necessary fields to both files used for calculations
mmh_spatial.make_geometries(sp, method = 'simple')
mmh_spatial.make_geometries(sf, method = 'simple')

## The files can now be passed to the main functions
## pass your own building_dictionary to use different dimensions for missing middle housing
ad = mmh_spatial.addon_feasibility(sp, sf, method = 'simple', building_dictionary = None)
nd = mmh_spatial.development_feasibility(sp, building_dictionary = None)

## Both the above export layers that can be used, however
## Since the parcel layer has been simplified, the below regions the information from the calculations
## to the oritinal parcel file. Running it on the same file twice adds both addon development and new development to the same file
parcel_out = mmh_spatial.parcel_rejoin(parcel, ad)
parcel_out = mmh_spatial.parcel_rejoin(parcel_out, nd)

## Conversion feasibility requires a non-simplified version of the footprint layer
## since it is building type specific. The defaults for the method pertain to an OSM layer,
## but you can specify different columns and values if a different layer was used
cf = mmh_spatial.simplify_footprints(foot, method = 'None')
mmh_spatial.make_geometries(cf, method = 'simple')
cl = mmh_spatial.conversion_feasibility(cf)

## Since converstion feasibility is building specific a different join function is required
## to add it to the parcel layer (in case of multiple garages/sheds on the same property)
## it can also be used individually to look at the specific buildings that have potential to be converted
## but this should be joined with land use to confirm

parcel_out.to_file('mmh_parcel_files')
cl.to_file('building_conversion_files')
