from rest_framework import serializers
from .models import Flight, Stat

class StatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stat
        fields = ['key', 'value']

class FlightSerializer(serializers.ModelSerializer):
    stats = StatSerializer(many=True, read_only=True)

    class Meta:
        model = Flight
        fields = ['master_index', 'before_after', 'date_diff', 'flight_length', 'label', 'hierarchy', 'number_flights_before', 'stats']