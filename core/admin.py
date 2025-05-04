from django.contrib import admin
from .models import City, Region, District, Town, Neighborhood

# Admin interface for City (Country)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Admin interface for Region
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    list_filter = ('country',)
    search_fields = ('name',)

# Admin interface for District
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    list_filter = ('region',)
    search_fields = ('name',)

# Admin interface for Town
class TownAdmin(admin.ModelAdmin):
    list_display = ('name', 'district')
    list_filter = ('district',)
    search_fields = ('name',)

# Admin interface for Neighborhood
class NeighborhoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'town')
    list_filter = ('town',)
    search_fields = ('name',)

# Register models with the admin interface
admin.site.register(City, CityAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Town, TownAdmin)
admin.site.register(Neighborhood, NeighborhoodAdmin)
