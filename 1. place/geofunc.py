def remove_equal_shpobj(objs):
    import rtree
    size = len(objs)
    equal_pair = []
    keep = []
    exclude_idx = set()

    tree_idx = rtree.index.Index()
    objs_bounds = [o.bounds for o in objs]
    for i in xrange(size):
        try:
            tree_idx.insert(i, objs_bounds[i])
        except Exception as e:
            print i, objs_bounds[i], objs[i]
            raise e

    for i in xrange(size):
        if i in exclude_idx:
            continue
        keep.append(i)
        js = tree_idx.intersection(objs[i].bounds)
        for j in js:
            if i!=j and objs[i].equals(objs[j]):
                equal_pair.append((i,int(j)))
                exclude_idx.add(j)

    return keep, equal_pair



def merge_within(shp_gpdf):
    import geopandas as gp
    import pandas as pd
    import datetime
    from other_utils import find_tree
    print 'begin merge within', datetime.datetime.now()
    keep, equal_pair= remove_equal_shpobj(shp_gpdf.geometry.values)
    equal_pair_index = [(shp_gpdf.iloc[i].name, shp_gpdf.iloc[j].name) for i, j in equal_pair]
    gpdf_no_equal = shp_gpdf.iloc[keep]
    print 'keep =',len(keep), 'equal pair =',len(equal_pair), gpdf_no_equal.shape, datetime.datetime.now()
    sjoin = gp.tools.sjoin(gpdf_no_equal,gpdf_no_equal,op='within')
    print 'sjoin.shape =',sjoin.shape, datetime.datetime.now()
    tree_all_parent = pd.DataFrame(zip(sjoin.index.values, sjoin.index_right.values), columns=['node','parent'])
    print 'messy tree shape =', tree_all_parent.shape, datetime.datetime.now()
    tree_direct_parent = find_tree(tree_all_parent.copy())
    print 'clean tree shape =', tree_direct_parent.shape, datetime.datetime.now()
    top_level_shp_idx = tree_direct_parent[tree_direct_parent.parent==-1].node.values
    return shp_gpdf[shp_gpdf.index.isin(top_level_shp_idx)], tree_all_parent, tree_direct_parent, equal_pair_index

def merge_within_by_list_shp(list_shp):
    import geopandas as gp
    import pandas as pd
    from other_utils import find_tree
    gpdf = gp.GeoDataFrame(list_shp,columns=['geometry'])
    sjoin = gp.tools.sjoin(gpdf,gpdf,op='within')
    messy_tree_df = pd.DataFrame(zip(sjoin.index.values, sjoin.index_right.values), columns=['node','parent'])
    clean_tree_df = find_tree(messy_tree_df)
    top_level_shp_idx = clean_tree_df[clean_tree_df.parent==-1].node.values
    return gpdf[gpdf.index.isin(top_level_shp_idx)].values

def grid_line(mini, maxi, ngrid=10):
    delta = (maxi-mini)/ngrid
    return [(mini+i*delta, mini+(i+1)*delta) for i in range(ngrid)] 


def grid_area(sw, ne, ngrid=10):
    grid_lat = grid_line(sw[0], ne[0], ngrid)
    grid_lon = grid_line(sw[1], ne[1], ngrid)
    grids = []
    for i in range(ngrid):
        for j in range(ngrid):
            s, n = grid_lat[i]
            w, e = grid_lon[j]
            grids.append(((s,w),(n,e)))
    return grids
    

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    from math import radians, cos, sin, asin, sqrt
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    m = km *1000
    return m

