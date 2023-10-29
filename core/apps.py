from django.apps import AppConfig
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from imap_tools import MailBox, A, AND
from bs4 import BeautifulSoup as BS
import threading, time, traceback, re, os

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def start_cron(self):
        from core.models import PaymentProccess
        
        while True:
            try:
                with MailBox('imap.ethereal.email').login(settings.ETHEREAL_EMAIL, settings.ETHEREAL_PASSWORD) as mailbox:
                    msgs = mailbox.fetch(A(AND(from_ = 'tanya@jago.com', subject = 'Asik, kamu telah menerima sejumlah uang', seen = False)), mark_seen = True)
                    for msg in msgs:
                        soup = BS(msg.html, 'html.parser')
                        data = soup.find('p', class_ = 'transfer-table-content', string = lambda x: x and re.match(r'^Rp[\d\.]+$', x))
                        total = int(re.sub(r'\D', '', data.text))
                        print(total)
                        if total:
                            payment_procces = PaymentProccess.objects.annotate(
                                unique_amount = F('payment__bill__amount') + F('unique_code')
                            ).filter(
                                expired__gt = timezone.now()
                            ).filter(
                                unique_amount = total
                            ).first()
                            if payment_procces:
                                payment_procces.payment.payed_time = timezone.now()
                                payment_procces.payment.save()

            except:
                traceback.print_exc()
            finally:
                time.sleep(120)

    def start_cron_2(self):
        from core.models import Bill, User, Payment
        
        while True:
            try:
                users = User.objects.filter(is_staff = True).filter(is_superuser = False).filter(is_active = True)
                unix_date_for_month = time.time() // 86400 * 31 # 31 days
                if not Bill.objects.filter(unix_date_for_month = unix_date_for_month).exists() and users:
                    with transaction.atomic():
                        bill = Bill()
                        bill.unix_date_for_month = unix_date_for_month
                        bill.amount = settings.AMOUNT_TO_PAY_PER_MONTH
                        bill.save()

                        for user in users:
                            payment = Payment()
                            payment.user = user
                            payment.bill = bill
                            payment.save()

            except:
                traceback.print_exc()
            finally:
                time.sleep(3600)

    def ready(self):
        super().ready()

        if os.environ.get('DJANGO_CORE_RUN_ONCE'):
            return
        
        os.environ['DJANGO_CORE_RUN_ONCE'] = 'True'

        threading.Thread(target = self.start_cron, daemon = True).start()
        threading.Thread(target = self.start_cron_2, daemon = True).start()
