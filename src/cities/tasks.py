from my_celery.celery_app import app
from web.models import Place
from cities.models import District


@app.task
def add_districts_to_venues(city_id):
    places = Place.objects.filter(new_city__pk=city_id)
    for place in places:
        place.save()


@app.task
def delete_districts_from_venues(city_id):
    places = Place.objects.only('district__id').filter(new_city__pk=city_id, district__isnull=False)
    district_ids = places.values_list('district__id')
    districts = District.objects.filter(id__in=district_ids)
    for district in districts:
        district.delete()
