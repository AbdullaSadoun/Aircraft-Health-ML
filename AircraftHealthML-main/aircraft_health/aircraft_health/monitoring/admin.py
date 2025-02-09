from django.contrib import admin
from .models import Flight, Stat

# Register your models here.
@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('master_index', 'label', 'before_after', 'date_diff', 'flight_length')
    search_fields = ('label', 'before_after')

@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ('flight', 'key', 'value')
    search_fields = ('key',)
