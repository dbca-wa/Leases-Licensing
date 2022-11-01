from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from leaseslicensing.components.approvals.models import Approval
from ledger.accounts.models import EmailUser
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from leaseslicensing.components.approvals.email import (
    send_approval_eclass_expiry_email_notification,
)

import itertools

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send Approval expiry notice for extended eclass licence when approval is due to expire in 18 months"

    def handle(self, *args, **options):
        logger.info("Running command {}")
        try:
            user = EmailUser.objects.get(email=settings.CRON_EMAIL)
        except:
            user = EmailUser.objects.create(email=settings.CRON_EMAIL, password="")

        errors = []
        updates = []
        today = timezone.localtime(timezone.now()).date()
        expiry_notification_date = today + relativedelta(months=+18)
        application_type_name = "E Class"
        expiry_conditions = {
            "expiry_date__lte": expiry_notification_date,
            "expiry_notice_sent": False,
            "replaced_by__isnull": True,
            "extended": True,
            "current_proposal__application_type__name": application_type_name,
        }
        logger.info("Running command {}".format(__name__))

        qs = Approval.objects.filter(**expiry_conditions)
        logger.info("{}".format(qs))
        for a in qs:
            if (
                a.status == "extended"
                or a.status == "current"
                or a.status == "suspended"
            ):
                try:
                    send_approval_eclass_expiry_email_notification(a)
                    a.expiry_notice_sent = True
                    a.save()
                    logger.info("Expiry notice sent for Approval {}".format(a.id))
                    updates.append(a.lodgement_number)
                except Exception as e:
                    err_msg = "Error sending expiry notice for Approval {}".format(
                        a.lodgement_number
                    )
                    logger.error("{}\n{}".format(err_msg, str(e)))
                    errors.append(err_msg)

        cmd_name = __name__.split(".")[-1].replace("_", " ").upper()
        err_str = (
            '<strong style="color: red;">Errors: {}</strong>'.format(len(errors))
            if len(errors) > 0
            else '<strong style="color: green;">Errors: 0</strong>'
        )
        msg = "<p>{} completed. Errors: {}. IDs updated: {}.</p>".format(
            cmd_name, err_str, updates
        )
        logger.info(msg)
        print(msg)  # will redirect to cron_tasks.log file, by the parent script
