import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
import numpy as np
import osmnx as ox
from osmnx.projection import project_gdf

default_accessory = {'adu': (3.05, 4.57)}
default_development = {'duplex': (16.76, 33.53),
                     'triplex': (12.19, 32.0),
                     'fourplex': (15.24, 36.58),
                     'townhouse': (3.05, 7.62),
                     'multiplex': (28.96, 35.05),
                     'cottage court': (33.53, 45.72)}

## Convert default dictionaries from feet to meters
# def meters_conversion(dict):
#     for key, itm in dict.items():
#         l, w = itm
#         lm = round(l * 0.3048, 2)
#         wm = round(w * 0.3048, 2)
#         dict[key] = (lm, wm)
#     print(dict)
#
# meters_conversion(default_accessory)
# meters_conversion(default_development)

def get_osm_footprints(area, save = True):
    if isinstance(area, gpd.GeoDataFrame):
        tgdf = area.to_crs(epsg = 4326)
        west, south, east, north = tgdf.total_bounds
    else:
        west, south, east, north = area
    gdf = ox.geometries.geometries_from_bbox(north, south, east, west, tags={'building':True})
    if save:
        gdf.reset_index()[['osmid', 'building', 'geometry']].to_file(save if save != True else 'Footprints')
    return gdf

def simplify_footprints(foot_layer, method = 'None', reproject = True):
    if reproject:
        foot_layer = project_gdf(foot_layer)

    if method == 'None':
        fl = foot_layer.reset_index(drop = True).reset_index().copy()
        fl.rename(columns = {'index' : 'foot_id'}, inplace = True)
        return fl
    elif method == 'Simple':
        fl = foot_layer.dissolve().explode(ignore_index = True, index_parts = False)
        fl = fl.reset_index(drop = True).reset_index().copy()
        fl.rename(columns = {'index' : 'foot_id'}, inplace = True)
        return fl

def simplify_parcel(parcel_layer, method = 'None', reproject = True, footprint = None):
    if reproject:
        parcel_layer = project_gdf(parcel_layer)

        if method == 'None':
            pl = parcel_layer.reset_index(drop = True).reset_index().copy()
            pl.rename(columns = {'index' : 'parcel_id'}, inplace = True)
            return pl
        elif method == 'simple':
            pl = parcel_layer.drop_duplicates(subset = 'geometry')
            pl = pl.explode(ignore_index = True, index_parts = False)
            pl = pl.reset_index(drop = True).reset_index().copy()
            pl.rename(columns = {'index' : 'parcel_id'}, inplace = True)
            return pl
        elif method == 'footprint overlay':
            pass
            '''TODO:
            write function that overlays footprint layer (simplified)
            checks percentage coverage of each one
            and merges parcels if > x overlap
            (i.e. duplex spanning two properties)'''

def make_geometries(gdf, method = 'simple'):
    gdf['Original'] = gdf.geometry
    gdf['Bounding'] = gdf.geometry.apply(lambda x: x.minimum_rotated_rectangle)
    gdf['Centroid'] = gdf.geometry.centroid

    gdf[['width', 'height']] = gdf.apply(assign_orientation, args = [method], axis = 1, result_type = 'expand')


def assign_orientation(r, method = 'simple'):
    if method == 'street orientation':
        pass
        '''TODO:
        calculate which edge of rectangle fronts the street
        assign that edge as "width"
        '''
    elif method == 'simple':
        a, b, c, _, _ = r.Bounding.exterior.coords
        len_list = []
        len1 = Point(a).distance(Point(b))
        len2 = Point(b).distance(Point(c))
        len_list.append(len1)
        len_list.append(len2)
        width = min(len_list)
        height = max(len_list)
        return width, height

def lot_comp(test_width, test_height, actual_width, actual_height, directional = True):
    if directional:
        if test_width <= actual_width and test_height <= actual_height:
            return True
        else:
            return False
    else:
        if (test_width <= actual_width and test_height <= actual_height) or (test_width <= actual_height and test_height <= actual_width):
            return True
        else:
            return False

def addon_feasibility(sp, sf, method = 'simple', building_dictionary = None):
    sf_cent = gpd.GeoDataFrame(sf.copy(), crs = sf.crs, geometry = sf.Centroid)
    sf_cent = sf_cent[['foot_id', 'width', 'height', 'geometry', 'Centroid']].copy()

    sp = sp[['parcel_id', 'width', 'height', 'geometry', 'Centroid']].copy()

    df = sp.sjoin(sf_cent, how = 'left', predicate = 'contains')
    df.rename(columns = {'width_left' : 'parcel_width', 'height_left' : 'parcel_height', 'Centroid_left' : 'parcel_centroid', 'width_right' : 'footprint_width', 'height_right' : 'footprint_height', 'Centroid_right' : 'footprint_centroid'}, inplace = True)

    if not building_dictionary:
        building_dictionary = default_accessory

    if method == 'simple':
        df['foot_area'] = df.footprint_width * df.footprint_height
        df.sort_values('foot_area', ascending = False, inplace = True)
        df = df.groupby('parcel_id').agg({'parcel_width' : 'first', 'parcel_height' : 'first', 'geometry' : 'first', 'parcel_centroid' : 'first', 'footprint_width' : 'first', 'footprint_height' : 'sum', 'footprint_centroid' : 'first'}).reset_index()
        df = gpd.GeoDataFrame(df, geometry = 'geometry', crs = sp.crs)
        df['centroid_displacement'] = df.apply(lambda r: r.parcel_centroid.distance(r.footprint_centroid) if pd.notnull(r.parcel_centroid) and pd.notnull(r.footprint_centroid) else np.nan, axis = 1)

        for idx, val in df.iterrows():
            for keys, itms in building_dictionary.items():
                max_displacement = val['parcel_height']/2 - val['footprint_height']/2
                cent_displacement_percentage = val['centroid_displacement'] / max_displacement

                max_height = val['parcel_height'] - val['footprint_height']
                true_height = (max_height / 2) + cent_displacement_percentage * (max_height / 2)

                df.loc[idx, '{0}'.format(keys)] = lot_comp(itms[0], itms[1], val['parcel_width'], true_height, directional = False)

        return_list = ['parcel_id', 'geometry']
        for key in building_dictionary.keys():
            return_list.append(key)
        return df[return_list]

    else:
        pass
        '''TODO:
        Isolate individual buildings that are on the property
        Map each of them out and determine types of space left over
        '''

def development_feasibility(sp, building_dictionary = None):
    if not building_dictionary:
        building_dictionary = default_development

    for idx, val in sp.iterrows():
        for keys, itms in building_dictionary.items():
            sp.loc[idx, '{0}'.format(keys)] = lot_comp(itms[0], itms[1], val['width'], val['height'])

    return_list = ['parcel_id', 'geometry']
    for key in building_dictionary.keys():
        return_list.append(key)
    return sp[return_list]

def conversion_feasibility(foot_layer, foot_column = 'building', foot_values = ['garage', 'shed'], building_dictionary = None):
    if not building_dictionary:
        building_dictionary = default_accessory

    cl = foot_layer[foot_layer[foot_column].isin(foot_values)].copy()
    cl = cl.reset_index(drop = True).reset_index()
    cl.rename(columns = {'index' : 'conversion_id'}, inplace = True)

    for idx, val in cl.iterrows():
        for keys, itms in building_dictionary.items():
            cl.loc[idx, 'conversion_{0}'.format(keys)] = lot_comp(itms[0], itms[1], val['width'], val['height'], directional = False)

    return_list = ['conversion_id', 'geometry']
    for key in building_dictionary.keys():
        return_list.append(f'conversion_{key}')
    return cl[return_list]


def parcel_rejoin(parcel_layer, join_layer, drop_duplicates = True):
    if drop_duplicates:
        parcel_layer.drop_duplicates(subset = ['geometry'], inplace = True)
    if parcel_layer.crs != join_layer.crs:
        parcel_layer.to_crs(join_layer.crs, inplace = True)
    join_cent = gpd.GeoDataFrame(join_layer.copy(), geometry = join_layer.representative_point(), crs = join_layer.crs)
    out_layer = parcel_layer.sjoin(join_cent, predicate = 'contains', how = 'left')
    out_layer.drop(columns = ['index_right'], inplace = True)
    return out_layer

# def mmh_analysis(parcel_layer, foot_layer, reproject = True, parcel_method = 'simple', orientation_method = 'simple', addon_method = 'simple', addon_dictionary = None, newdev_dictionary = None):
#     sf = simplify_footprints(foot_layer, reproject = reproject)
#     sp = simplify_parcel(parcel_layer, reproject = reproject, method = parcel_method, footprint = sf)
#
#     make_geometries(sp, method = orientation_method)
#     make_geometries(sf, method = orientation_method)
#
#     ad = addon_feasibility(sp, sf, method = addon_method, building_dictionary = addon_dictionary)
#     nd = development_feasibility(sp, building_dictionary = newdev_dictionary)
#
#     parcel_out = parcel_rejoin(parcel_layer, ad)
#     parcel_out = parcel_rejoin(parcel_out, nd)
#
#     return parcel_out
