from django.contrib import admin
from freight_shipping.models import Payment


class PaymentAdmin(admin.ModelAdmin):
    pass


admin.site.register(Payment, PaymentAdmin)
