# coding=utf-8
import geopandas as gp





def clean_place(x):
    if '##' in x:
        x = x.split('##')[0]
    x = x[:-1] if x[-1].isdigit() else x
    return x.replace(' ', '_')



def uk_crs():
    min_lat = 59.066574
    max_lon = -8.089235
    max_lat = 50.126911
    min_lon = 1.793197
    lon_0 = (max_lon + min_lon) / 2
    lat_0 = (max_lat + min_lat) / 2
    return {'datum': 'WGS84', 'no_defs': True, 'proj': 'aea', 'lat_1': min_lat, 'lat_2': max_lat, 'lat_0': lat_0,
            'lon_0': lon_0}


def us_crs():
    return {'proj': 'aea', 'lat_1': 29.5, 'lat_2': 45.5, 'lat_0': 37.5, 'lon_0': -96,
            'x_0': 0, 'y_0': 0, 'datum': 'NAD83', 'units': 'm', 'no_defs': True}


def cal_area(geojson_path, area_path, target_crs):
    polys = gp.read_file(geojson_path)
    polys['area'] = polys.to_crs(crs=target_crs).geometry.apply(lambda x: x.area)
    polys.place = polys.place.apply(clean_place)
    places = polys.groupby('place').agg(sum).reset_index()[['place','area']]
    places.to_csv(area_path)
    return places


def main():
    root_data_dir = '../data'
    poly_m_path = root_data_dir + '/place_polys_m.geojson'
    poly_np_path = root_data_dir + '/place_polys_np.geojson'
    area_m_path = root_data_dir + '/place_m_area.csv'
    area_np_path = root_data_dir + '/place_np_area.csv'

    area_m = cal_area(poly_m_path,area_m_path, uk_crs())
    area_np = cal_area(poly_np_path,area_np_path, us_crs())

    return area_m, area_np

if __name__ == '__main__':
    main()

