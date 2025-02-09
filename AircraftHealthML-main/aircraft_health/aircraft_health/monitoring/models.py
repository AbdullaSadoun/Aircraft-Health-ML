from django.db import models

class Flight(models.Model):
    master_index = models.IntegerField(primary_key=True, db_index=True)
    before_after = models.CharField(max_length=10, db_index=True)  # 'before', 'after', 'same'
    date_diff = models.IntegerField(db_index=True)
    flight_length = models.IntegerField(db_index=True)
    label = models.CharField(max_length=255, db_index=True)
    hierarchy = models.CharField(max_length=255, blank=True, null=True)
    number_flights_before = models.IntegerField()

    def __str__(self):
        return f"Flight {self.master_index} - {self.label}"

class Stat(models.Model):
    flight = models.ForeignKey(Flight, related_name='stats', on_delete=models.CASCADE)
    key = models.CharField(max_length=50)
    value = models.FloatField()

    def __str__(self):
        return f"Stat for Flight {self.flight.master_index} - {self.key}"
