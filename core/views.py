from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from django.http import HttpRequest, Http404
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from core.models import PaymentProccess, Payment

@login_required
def pay(request: HttpRequest, pk: int):
    context = admin.site.each_context(request)
    context['title'] = 'Bayar'

    payment = Payment.objects.filter(pk = pk).first()
    if not payment:
        raise Http404
    
    # payment_proccess = PaymentProccess()
    # payment_proccess.payment = payment
    # payment_proccess.save()

    payment_proccess, _ = PaymentProccess.objects.get_or_create(
        expired__gte = timezone.now(),
        defaults = {
            'payment_id': payment.pk,
        }
    )

    context['payment_proccess'] = payment_proccess
    context['total_amount'] = payment_proccess.payment.bill.amount + payment_proccess.unique_code
    context['name_rekening'] = settings.NAME_REKENING
    context['no_rekening'] = settings.NO_REKENING

    return render(request, 'admin/pay.html', context)