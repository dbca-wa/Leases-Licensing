""" Should be run each day after the cron task that updates the compliance status """
import logging
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from leaseslicensing.components.compliances.email import (
    send_compliance_preventing_transfer_notification_email,
)
from leaseslicensing.components.compliances.models import Compliance

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Send notification emails for compliances which have past their due dates, "
        "and also reminder notification emails for those that are within the daterange "
        "prior to due_date (eg. within 14 days of due date)"
    )

    def handle(self, *args, **options):
        try:
            user = EmailUser.objects.get(email=settings.CRON_EMAIL)
        except EmailUser.DoesNotExist:
            user = EmailUser.objects.create(email=settings.CRON_EMAIL, password="")

        errors = []
        reminders_sent = []

        logger.info(f"Running command {__name__}")
        for c in Compliance.objects.filter(
            processing_status__in=[
                Compliance.PROCESSING_STATUS_DUE,
                Compliance.PROCESSING_STATUS_OVERDUE,
            ]
        ):
            try:
                if c.send_reminder(user.id):
                    reminders_sent.append(c.lodgement_number)
                if c.approval.has_pending_transfer:
                    send_compliance_preventing_transfer_notification_email(c)
            except Exception as e:
                err_msg = "Error sending Reminder Compliance {}\n".format(
                    c.lodgement_number
                )
                logger.error(f"{err_msg}\n{str(e)}\n{str(traceback.format_exc())}")
                errors.append(err_msg)

        cmd_name = __name__.split(".")[-1].replace("_", " ").upper()
        err_str = (
            f'<strong style="color: red;">Errors: {len(errors)}</strong>'
            if len(errors) > 0
            else '<strong style="color: green;">Errors: 0</strong>'
        )
        msg = "<p>{} completed. Errors: {}. Reminders sent for the following compliances: {}.</p>".format(
            cmd_name, err_str, reminders_sent
        )
        logger.info(msg)
        self.stdout.write(
            msg
        )  # will redirect to cron_tasks.log file, by the parent script
