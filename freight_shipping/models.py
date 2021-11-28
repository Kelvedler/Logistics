from django.db import models
from users.models import User
from django.core import exceptions


class Country(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name_plural = "Countries"
        default_permissions = ()

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=60, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Cities"
        default_permissions = ()

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=60, unique=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name


class VehicleModel(models.Model):
    name = models.CharField(max_length=60)
    length = models.PositiveSmallIntegerField()
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    maximum_payload = models.PositiveSmallIntegerField()

    class Meta:
        default_permissions = ()

    def __str__(self):
        return f'{self.name} [capacity: {self.length}x{self.width}x{self.height}mm, payload: {self.maximum_payload}kg]'


class Vehicle(models.Model):
    plate = models.CharField(max_length=20, unique=True)
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.RESTRICT)
    temperature_control = models.BooleanField(default=False)
    dangerous_goods = models.BooleanField(default=False)
    driver = models.OneToOneField(User, null=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(District, on_delete=models.RESTRICT)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.plate


class Route(models.Model):
    location = models.ForeignKey(District, on_delete=models.CASCADE)
    next_route_id = models.PositiveSmallIntegerField(null=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='route')

    class Meta:
        default_permissions = ()

    def __str__(self):
        return f'{self.location} ({self.vehicle})'


class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    departure_route = models.ForeignKey(Route, null=True, on_delete=models.SET_NULL, related_name='departure_route')
    destination_route = models.ForeignKey(Route, null=True, on_delete=models.SET_NULL, related_name='destination_route')
    departure_district = models.ForeignKey(District, on_delete=models.RESTRICT, related_name='departure_district')
    destination_district = models.ForeignKey(District, on_delete=models.RESTRICT, related_name='destination_district')
    length = models.PositiveSmallIntegerField()
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    weight = models.PositiveSmallIntegerField()
    temperature_control = models.BooleanField(default=False)
    dangerous_goods = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()

    def __str__(self):
        return f'# {self.id}'


class CompletedOrder(models.Model):
    completed_at = models.DateTimeField(auto_now_add=True)
    departure = models.ForeignKey(District, on_delete=models.RESTRICT, related_name='departure')
    destination = models.ForeignKey(District, on_delete=models.RESTRICT, related_name='destination')
    driver = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='driver')
    customer = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='customer')

    class Meta:
        default_permissions = ()

    def __str__(self):
        return f'{self.departure} - {self.destination} order for {self.customer} by {self.driver} at {self.completed_at}'


class Payment(models.Model):
    order = models.OneToOneField(Order, null=True,  on_delete=models.SET_NULL)
    completed_order = models.OneToOneField(CompletedOrder, default=None, null=True, on_delete=models.RESTRICT)
    payment_method = models.CharField(max_length=20)
    payment_id = models.CharField(max_length=19)
    completed = models.BooleanField(default=False)
    currency_code = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        default_permissions = ()
        unique_together = ['payment_method', 'payment_id']

    def __str__(self):
        return f'{self.payment_method}; payment_id={self.payment_id}, completed={self.completed}'
