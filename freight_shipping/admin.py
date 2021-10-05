from django.contrib import admin
from .models import Country, City, District, Route, VehicleModel, RoadFreightPark, Order


class CountryAdmin(admin.ModelAdmin):
    pass


class CityAdmin(admin.ModelAdmin):
    pass


class DistrictAdmin(admin.ModelAdmin):
    pass


class RouteAdmin(admin.ModelAdmin):
    pass


class VehicleModelAdmin(admin.ModelAdmin):
    pass


class RoadFreightParkAdmin(admin.ModelAdmin):
    pass


class OrderAdmin(admin.ModelAdmin):
    pass


admin.site.register(Country, CountryAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Route, RouteAdmin)
admin.site.register(VehicleModel, VehicleModelAdmin)
admin.site.register(RoadFreightPark, RoadFreightParkAdmin)
admin.site.register(Order, OrderAdmin)
