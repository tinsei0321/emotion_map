"""Diagnose boundary shape and density patterns."""
import geopandas as gpd
from shapely.geometry import Polygon, Point

gdf = gpd.read_file(r'DATA\boundaries\规划范围\规划范围.shp')
gdf_wgs = gdf.to_crs('EPSG:4326')
geom = gdf_wgs.geometry.iloc[0]
poly = Polygon(geom.coords)

b = poly.bounds
print(f'Bounds: lon {b[0]:.4f}~{b[2]:.4f}, lat {b[1]:.4f}~{b[3]:.4f}')
print(f'Centroid: {poly.centroid.x:.4f}, {poly.centroid.y:.4f}')
print(f'Area (deg²): {poly.area:.6f}')

# Verify union_all vs Polygon
try:
    poly2 = gdf_wgs.geometry.union_all()
    print(f'\nunion_all type: {poly2.geom_type}, area={poly2.area:.6f}')
    # If union_all gives MultiPolygon or GeometryCollection, need to handle
    if poly2.geom_type == 'GeometryCollection':
        from shapely.geometry import Polygon as P2
        polys = [g for g in poly2.geoms if g.geom_type == 'Polygon']
        print(f'  Contains {len(polys)} polygons')
except Exception as e:
    print(f'  union_all error: {e}')

# Check if polygon is valid and not self-intersecting
print(f'\nPolygon valid: {poly.is_valid}')
print(f'Polygon is_simple: {poly.is_simple}')

# Try buffer(0) to fix
if not poly.is_valid:
    poly_fixed = poly.buffer(0)
    print(f'Fixed: type={poly_fixed.geom_type}, valid={poly_fixed.is_valid}')
    if poly_fixed.geom_type == 'MultiPolygon':
        poly = max(poly_fixed.geoms, key=lambda g: g.area)
        print(f'  Took largest polygon, area={poly.area:.6f}')

# Check the "blank" area - sample grid
print('\n--- Grid check for gaps ---')
for lon_step in range(20):
    lon_mid = b[0] + (lon_step + 0.5) * (b[2] - b[0]) / 20
    in_count = 0
    for lat_step in range(50):
        lat_mid = b[1] + (lat_step + 0.5) * (b[3] - b[1]) / 50
        if poly.contains(Point(lon_mid, lat_mid)):
            in_count += 1
    bar = '#' * in_count
    print(f'  lon={lon_mid:.4f} in={in_count:2d} {bar}')

# Check lat profile at a few longitudes
print('\n--- Lat profiles ---')
for test_lon in [111.29, 111.31, 111.33, 111.36, 111.40]:
    line = ''
    for j in range(200):
        lat = b[1] + j * (b[3] - b[1]) / 200
        line += '#' if poly.contains(Point(test_lon, lat)) else ' '
    # Mark approximate river position
    print(f'  lon={test_lon}: |{line}|')

# River approx: Yangtze flows at about lat 30.69-30.71 near city center
print('\n--- River exclusion test ---')
# Test a few points near the river
test_pts = [
    (111.30, 30.700, 'near CBD riverside'),
    (111.28, 30.695, 'near binjiang park'),
    (111.35, 30.690, 'wujiagang riverside'),
    (111.40, 30.662, 'near east station'),
    (111.32, 30.720, 'sanxia university north'),
    (111.28, 30.740, 'xiba/gezhouba'),
]
for lon, lat, desc in test_pts:
    in_bound = poly.contains(Point(lon, lat))
    print(f'  ({lon:.2f}, {lat:.3f}) {desc}: {"IN" if in_bound else "OUT"}')