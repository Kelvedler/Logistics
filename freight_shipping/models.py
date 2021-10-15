from django.db import models
from users.models import User

DEFAULT_DRIVER = 1
NO_NEXT_LOCATION = 0


class Country(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name_plural = "Countries"


class City(models.Model):
    name = models.CharField(max_length=60, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Cities"


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


class RoadFreightPark(models.Model):
    plate = models.CharField(max_length=20, unique=True)
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.RESTRICT)
    temperature_control = models.BooleanField(default=False)
    dangerous_goods = models.BooleanField(default=False)
    driver = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(District, on_delete=models.RESTRICT)
    route = models.ForeignKey(Route, null=True, on_delete=models.SET_NULL)


class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    route = models.ManyToManyField(Route, default=None)
    length = models.PositiveSmallIntegerField()
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    weight = models.PositiveSmallIntegerField()
    temperature_control = models.BooleanField()
    dangerous_goods = models.BooleanField()
