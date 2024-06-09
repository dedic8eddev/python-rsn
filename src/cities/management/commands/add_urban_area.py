import geopandas as gpd
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.core.management.base import BaseCommand
from pyproj import Proj, Transformer
from shapely.geometry import Point

from cities.models import UrbanArea, City

# Spatial projections
PSEUDO_MERCATOR_PROJ = Proj('epsg:3857')
LONLAT_PROJ = Proj('epsg:4326')
# conversion of lat/lon coordinates to web mercator
LONLAT_TO_PM = Transformer.from_proj(LONLAT_PROJ, PSEUDO_MERCATOR_PROJ, always_xy=True, skip_equivalent=True)


class UrbanAreaData:
    def __init__(self, path):
        self.gdf = gpd.read_file(f"zip://{path[0]}")

    def get_urban_area_by_point(self, point):
        point = Point(LONLAT_TO_PM.transform(*point.coords))
        ua = gpd.sjoin(self.gdf, gpd.GeoDataFrame(geometry=[point], crs=3857))
        return ua


class Command(BaseCommand):
    help = 'Adding Urbun Area to City'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', type=str)

    def handle(self, *args, **options):
        cs = City.objects.all()
        self.stdout.write(self.style.SUCCESS(cs.count()))
        urban_area_data = UrbanAreaData(options['path'])

        for zip_path in options['path']:
            self.stdout.write(self.style.SUCCESS('Path to zip file "%s"' % zip_path))
            i = 0
            for city in cs:
                self.stdout.write(self.style.SUCCESS('left {}'.format(cs.count() - i)))
                i += 1
                ua = urban_area_data.get_urban_area_by_point(city.location)
                if not ua.empty:
                    if len(ua) > 1:
                        ua = ua.loc[ua.URAU_CATG == 'K']
                    ua_list = ua.to_dict('records')
                    ua_item = ua_list[0]
                    geometry_gpd = ua_item.pop('geometry')
                    geometry = GEOSGeometry(str(geometry_gpd))
                    g_type = geometry.geom_type
                    self.stdout.write(self.style.SUCCESS('{}, \n----{}'.format(city.name, ua)))
                    null_polygon = Polygon(((0, 0), (0, 0), (0, 0), (0, 0)))
                    ua_kwargs = {
                        'country_code': city.country.code,
                        'category': ua.URAU_CATG.values[0],
                        'code': ua.URAU_CODE.values[0],
                        'geometry_polygon': geometry if g_type == 'Polygon' else null_polygon,
                        'geometry_multipolygon': geometry if g_type == 'MultiPolygon' else MultiPolygon(null_polygon),
                        'name': ua.URAU_NAME.values[0],
                        'region': city.region
                    }
                    (ua_obj, created) = UrbanArea.objects.get_or_create(**ua_kwargs)
                    city.urban_area = ua_obj
                    city.save()
