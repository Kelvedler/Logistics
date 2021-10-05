from django.db import models
from users.models import User

DEFAULT_DRIVER = 1
NO_NEXT_LOCATION = 0


class Country(models.Model):
    name = models.CharField(max_length=60, unique=True)


class City(models.Model):
    name = models.CharField(max_length=60, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class District(models.Model):
    name = models.CharField(max_length=60, unique=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)


class Route(models.Model):
    location = models.ForeignKey(District, on_delete=models.CASCADE)
    next_location = models.PositiveSmallIntegerField(default=NO_NEXT_LOCATION)


class VehicleModel(models.Model):
    name = models.CharField(max_length=60)
    length = models.PositiveSmallIntegerField()
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    maximum_payload = models.PositiveSmallIntegerField()


class VehicleOccupancy(models.Model):
    length = models.PositiveSmallIntegerField()
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    mass = models.PositiveSmallIntegerField()


class RoadFreightPark(models.Model):
    plate = models.CharField(max_length=20, unique=True)
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE)
    vehicle_occupancy = models.ForeignKey(VehicleOccupancy, on_delete=models.CASCADE)
    temperature_control = models.BooleanField(default=False)
    dangerous_goods = models.BooleanField(default=False)
    driver = models.ForeignKey(User, default=DEFAULT_DRIVER, on_delete=models.SET_DEFAULT)
    location = models.ForeignKey(District, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
