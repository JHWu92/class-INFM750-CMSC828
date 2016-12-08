import shapely.geometry as shpgeo
from geofunc import *
def node2pt(node):
    return shpgeo.Point(node.lon,node.lat)
def lonlat_in_way(way):
    coors = []
    for node in way.nodes:
        coors.append((node.lon, node.lat))
    return coors
def is_closed_way(way):
    return way.nodes[0] == way.nodes[-1]


def way2line(api, way,need_api=True):
    import time
    import overpy
    while True:
        try:
            if need_api:
                way = api.query("""
                way(%s);
                (._;>;);
                out;
                """% way.id).ways[0]
            break
        except overpy.exception.OverpassGatewayTimeout as e:
            print e
            time.sleep(10)
    coors = lonlat_in_way(way)
    return shpgeo.LineString(coors)


def get_relation(api, relation,need_api=True):
    import time
    import overpy
    while True:
        try:
            if need_api:
                relation = api.query("""
                relation(%s);
                (._;>;);
                out;
                """ % relation.id).relations[0]
            break
        except overpy.exception.OverpassGatewayTimeout as e:
            print e
            time.sleep(10)
    return relation


def rltn2dictShp(relation, sub_rltn=False):

    from shapely.ops import linemerge
    import overpy
    nodes, ways, sub_nodes, sub_ways = [], [], [], []
    for m in relation.members:
        obj = m.resolve()
        if isinstance(obj, overpy.Node):
            nodes.append(obj)
        elif isinstance(obj, overpy.Way):
            ways.append(obj)
        elif isinstance(obj, overpy.Relation):
            r_nodes, r_ways = rltn2dictShp(obj, True)
            sub_nodes.extend(r_nodes)
            sub_ways.extend(r_ways)
    if sub_rltn:
        return nodes, ways
    nodes.extend([node for node in sub_nodes])
    ways.extend([way for way in sub_ways])

    points = [node2pt(node) for node in nodes]
    keep_pts_idx, _ = remove_equal_shpobj(points)
    points = [p for cnt, p in enumerate(points) if cnt in keep_pts_idx]

    lines = [way2line(way,False) for way in ways]
    keep_lines_idx, _ = remove_equal_shpobj(lines)
    lines = [l for cnt, l in enumerate(lines) if cnt in keep_lines_idx]

    dict_shp= { 'LineString': [], 'Polygon': []}
    if lines:
        merged = linemerge(lines)
        if merged.type == 'LineString':
            merged = [merged]
        else:
            merged = list(merged)
        for ln in merged:
            if ln.is_ring:
                dict_shp['Polygon'].append(shpgeo.Polygon(ln))
            else:
                dict_shp['LineString'].append(ln)
    return dict_shp

def rltn2mergedListShp( relation):
    shpcltn = rltn2dictShp(relation)
    list_shp = []
    for l in shpcltn.values():
        list_shp += l
    merge_list_shp = merge_within_by_list_shp(list_shp)
    return merge_list_shp


def rltn2mergedFlattenListShp(relation):
    merge_list_shp = rltn2mergedListShp(relation)
    flat_shpcltn = []
    for shpobjs in merge_list_shp:
        flat_shpcltn.extend(shpobjs)
    return flat_shpcltn