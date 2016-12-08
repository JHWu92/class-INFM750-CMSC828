# coding=utf-8
import glob

from osmread import parse_file, Way, Relation
import overpy
import geopandas as gp

from osm_helper import *

OVER_API = overpy.Overpass()


def get_max_dis_from_center_to_ext(centr, ext_coords):
    lon1, lat1 = centr
    return max([haversine(lon1, lat1, lon2, lat2) for lon2, lat2 in ext_coords])


def get_cntr_radius(poly):
    cntr = poly.centroid.coords[0]
    ext_coords = poly.exterior.coords
    radius = get_max_dis_from_center_to_ext(cntr, ext_coords)
    return cntr, radius, ext_coords


def osm2polys(osm_data):
    if isinstance(osm_data, Way):
        ln = way2line(OVER_API,osm_data)
        poly = shpgeo.Polygon(ln)
        return [poly]
    if isinstance(osm_data, Relation):
        r = get_relation(OVER_API,osm_data)
        return rltn2mergedFlattenListShp(r)


def osms2flattenPolys(data_file_dir):
    place_polys = []
    for i, file_path in enumerate(glob.glob(data_file_dir + '/*')):
        _, place = file_path.split('\\')
        place = place[:-4].replace(' ', '_')
        osm_data = parse_file(file_path)
        osm_data = list(osm_data)
        assert len(osm_data) == 1, '{}th {}: len!=0'.format(i, file_path)
        print i, place, len(list(osm_data))
        osm_data = osm_data[0]
        polys = osm2polys(osm_data)
        for cnt, poly in enumerate(polys):
            cntr, radius, ext_coords = get_cntr_radius(poly)
            place_polys.append([i, '{}##{}'.format(place, cnt), cntr, radius + 1000, poly])

    print len(place_polys)
    return place_polys


def osm2geojson(xml_dir, poly_format, target_crs, crs_type, update_polys=False):
    poly_path = poly_format.format('')
    print 'get original osm to geopandas'
    if update_polys:
        place_polys = osms2flattenPolys(xml_dir)
        place_polys_gpdf = gp.GeoDataFrame(place_polys, columns=['id', 'place', 'cntr', 'radius', 'geometry'])
    else:
        place_polys_gpdf = gp.read_file(poly_path)

    place_polys_gpdf.crs = {'init': 'epsg:4326', 'no_defs': True}
    place_polys_gpdf.cntr = place_polys_gpdf.cntr.apply(str)
    if update_polys:
        with open(poly_path, 'w') as f:
            f.write(place_polys_gpdf.to_json())

    print 'get csv for tw crawler'
    place_polys_gpdf_tw = place_polys_gpdf.copy()
    place_polys_gpdf_tw['date_until'] = '2099-01-01'
    if update_polys:
        place_polys_gpdf_tw[['place', 'date_until', 'radius', 'cntr']].to_csv(poly_format.format('_tw'))

    def get_n_write_bfr_gpdf(gpdf, bfr, crs, file_path):
        if crs_type == 'crs':
            gpdf_bfr = gpdf.to_crs(crs=crs)
        else:
            gpdf_bfr = gpdf.to_crs(epsg=crs)
        gpdf_bfr.geometry = gpdf_bfr.buffer(bfr)
        gpdf_bfr = gpdf_bfr.to_crs(epsg=4326)
        joined = gp.tools.sjoin(gpdf_bfr, gpdf)
        lookup = joined[joined.id_left != joined.id_right][['id_left', 'id_right']].groupby('id_left').apply(
            lambda x: x.id_right.tolist()).to_dict()
        gpdf_bfr.geometry = gpdf_bfr.apply(lambda x: substract_overlap(x, gpdf, lookup), axis=1)
        if update_polys:
            with open(file_path, 'w')as f:
                f.write(gpdf_bfr.to_json())
        return gpdf_bfr

    print 'get differnt buffer geojson'
    place_polys_gpdf_bfr5 = get_n_write_bfr_gpdf(place_polys_gpdf, 5, target_crs,poly_format.format('_5m'))
    place_polys_gpdf_bfr10 = get_n_write_bfr_gpdf(place_polys_gpdf, 10, target_crs,poly_format.format('_10m'))
    place_polys_gpdf_bfr50 = get_n_write_bfr_gpdf(place_polys_gpdf, 50, target_crs,poly_format.format('_50m'))
    place_polys_gpdf_bfr100 = get_n_write_bfr_gpdf(place_polys_gpdf, 100, target_crs, poly_format.format('_100m'))

    return place_polys_gpdf_bfr100


def substract_overlap(subtrahend, origin_gpdf, lookup):
    sid, subtra_poly = subtrahend.id, subtrahend.geometry
    if sid in lookup:
        minuend = origin_gpdf[origin_gpdf.id.isin(lookup[sid])]
        for _, m_poly in minuend[['geometry']].itertuples():
            subtra_poly -= m_poly
    return subtra_poly


def map_for_np(place_polys_gpdf):
    import sys, os
    sys.path.insert(0, os.path.abspath('..'))
    from leaflet_creation_v2 import create_map_visualization
    # check whether there is obvious mistake of places,
    # for example, use the national protrait gallery in DC for the NPG in England
    html_title = 'usa np'
    file_name = 'usa np'
    lon, lat = -96, 37.5
    zoom = 4
    init_layers = ['streets', 'stsg_layer']
    map_layers = ['light', 'streets']
    binding_data = [['stsg', 'street segment']]
    place_polys_gpdf_vis = place_polys_gpdf.copy()
    place_polys_gpdf_vis['color'] = '#F00'
    gpdfs = [place_polys_gpdf_vis]
    create_map_visualization(html_title, file_name, lat, lon, zoom, init_layers, map_layers, binding_data, gpdfs)


def map_for_m(place_polys_gpdf):
    import sys, os
    sys.path.insert(0, os.path.abspath('..'))
    from leaflet_creation_v2 import create_map_visualization
    # check whether there is obvious mistake of places,
    # for example, use the national protrait gallery in DC for the NPG in England
    html_title = 'uk m'
    file_name = 'uk m'
    lon, lat = -0.17869653562200458, 51.49451759485569
    zoom = 8
    init_layers = ['streets', 'stsg_layer']
    map_layers = ['light', 'streets']
    binding_data = [['stsg', 'street segment']]
    place_polys_gpdf_vis = place_polys_gpdf.copy()
    place_polys_gpdf_vis['color'] = '#F00'
    gpdfs = [place_polys_gpdf_vis]
    create_map_visualization(html_title, file_name, lat, lon, zoom, init_layers, map_layers, binding_data, gpdfs)



def main():
    root_data_dir = '../data'

    np_xml_dir = root_data_dir + '/OSM_national_park@US/'
    polys_np_format = root_data_dir + '/place_polys_np{}.geojson'
    usa_crs = {'proj': 'aea', 'lat_1': 29.5, 'lat_2': 45.5, 'lat_0': 37.5, 'lon_0': -96,
               'x_0': 0, 'y_0': 0, 'datum': 'NAD83', 'units': 'm', 'no_defs': True}

    print 'begin np'
    np_gpdf = osm2geojson(np_xml_dir, polys_np_format, usa_crs, 'crs')

    print 'get map for np'
    map_for_np(np_gpdf)

    m_xml_dir = root_data_dir + '/OSM_museum@England/'
    polys_m_format = root_data_dir + '/place_polys_m{}.geojson'
    uk_epsg = 27700
    print 'begin m'
    m_gpdf = osm2geojson(m_xml_dir, polys_m_format, uk_epsg, 'epsg')

    print 'get map for m'
    map_for_m(m_gpdf)


if __name__ == '__main__':
    main()
