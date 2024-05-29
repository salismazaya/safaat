from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

class Bill(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'Tagihan'

    name = models.CharField(max_length = 255, verbose_name = 'Nama Tagihan')
    unix_date_for_month = models.IntegerField(unique = True, editable = False, null = True, blank = True)
    date = models.DateField(default = timezone.now)
    amount = models.PositiveBigIntegerField()

    def __str__(self):
        return self.name


class Payment(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = 'Pembayaran'

    user = models.ForeignKey(User, on_delete = models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete = models.CASCADE)
    payed_time = models.DateTimeField(null = True, blank = True, verbose_name = 'Dibayar Pada')

def _get_default_expired():
    return timezone.now() + timedelta(days = 1)


class PaymentProccess(models.Model):
    payment = models.ForeignKey(Payment, on_delete = models.CASCADE)
    expired = models.DateTimeField(default = _get_default_expired)
    unique_code = models.PositiveBigIntegerField()

    def save(self, *args, **kwargs):
        while True:
            with transaction.atomic():
                unique_code = random.randint(0,1000)
                if not PaymentProccess.objects.annotate(
                    unique_amount = models.F('payment__bill__amount') + models.F('unique_code') + models.Value(unique_code)
                ).filter(
                    expired__gt = timezone.now()
                ).filter(
                    unique_amount = unique_code + self.payment.bill.amount
                ).exists():
                    break
        
        self.unique_code = unique_code
        super().save(*args, **kwargs)