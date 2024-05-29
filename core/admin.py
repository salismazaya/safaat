from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from core.models import Payment, Bill, User
from django.utils.safestring import mark_safe
from django.db import transaction

class HasPaidFilter(admin.SimpleListFilter):
    title = 'Sudah Dibayar?'
    parameter_name = 'has_paid'

    def lookups(self, request, model_admin):
        return [
            ('1', 'Sudah'),
            ('0', 'Belum'),
        ]
    
    def queryset(self, request, queryset: QuerySet):
        if self.value() == '1':
            return queryset.filter(payed_time__isnull = False)

        if self.value() == '0':
            return queryset.filter(payed_time__isnull = True)

        return queryset
    
class BillFilter(admin.SimpleListFilter):
    title = 'Tagihan'
    parameter_name = 'bill'

    def lookups(self, request, model_admin):
        rv = []

        for bill in Bill.objects.order_by('-id'):
            rv.append(
                (
                    str(bill.pk),
                    str(bill),
                )
            )
        
        return rv
    
    def queryset(self, request, queryset: QuerySet):
        if not self.value():
            return queryset

        return queryset.filter(bill__pk = self.value())

class PaymentAdmin(admin.ModelAdmin):
    fields = ('user', 'payed_time')
    list_display = ('id', 'user', 'name', 'bill_', 'has_paid', 'payed_time', 'pay_button')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('payed_time', HasPaidFilter, BillFilter)

    def get_queryset(self, request: HttpRequest):
        self.request = request
        queryset = super().get_queryset(request)

        if not request.user.is_superuser:
            queryset = queryset.filter(user__id = self.request.user.id)

        return queryset   


    def has_paid(self, obj: Payment):
        return bool(obj.payed_time)
    
    def bill_(self, obj: Payment):
        return obj.bill.__str__()
    
    def name(self, obj: Payment):
        return ' '.join([obj.user.first_name, obj.user.last_name])
    
    def pay_button(self, obj: Payment):
        if self.request.user.pk != obj.user.pk:
            return '-'

        if self.has_paid(obj):
            return '-'

        return mark_safe(f'<a href="/pay/{obj.pk}/" class="btn btn-primary">Bayar</a>')


    bill_.short_description = 'Tagihan'
    has_paid.boolean = True
    has_paid.short_description = 'Sudah Dibayar?'
    name.short_description = 'Nama'
    pay_button.short_description = 'Tombol'


class BillAdmin(admin.ModelAdmin):
    @transaction.atomic
    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        super().save_model(request, obj, form, change)
        users = User.objects.filter(is_staff = True).filter(is_superuser = False).filter(is_active = True)
        for user in users:
            payment = Payment()
            payment.bill = obj
            payment.user = user
            payment.save()


admin.site.register(Payment, PaymentAdmin)
admin.site.register(Bill, BillAdmin)
