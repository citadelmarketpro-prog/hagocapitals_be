"""
Nudges users who started a deposit (hit "Continue" on the amount step, which
records a DepositIntent) but never submitted the real deposit, once the
attempt has sat abandoned for at least REMINDER_DELAY_MINUTES — mirrors the
"did life get in the way?" abandoned-payment nudge popular apps send. Each
abandoned attempt produces both an email and a distinct in-app
Notification (notif_type="abandoned_deposit") the frontend surfaces as a
one-time popup until dismissed.

Meant to run frequently via cron (e.g. every minute); the reminder_sent_at
guard means each abandoned intent only ever triggers one nudge no matter how
often the command runs — a tight schedule just controls how promptly it
fires once the delay has passed.

Usage:
    python manage.py send_deposit_reminders
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import DepositIntent, Notification
from core.email_service import send_deposit_reminder_email

REMINDER_DELAY_MINUTES = 7
# Ignore intents older than this even if never reminded — guards against a
# burst of stale emails if the cron was ever down for a while.
MAX_AGE_HOURS = 24


class Command(BaseCommand):
    help = "Email users who started a deposit but never completed it."

    def handle(self, *args, **options):
        now = timezone.now()
        cutoff = now - timedelta(minutes=REMINDER_DELAY_MINUTES)
        oldest = now - timedelta(hours=MAX_AGE_HOURS)

        eligible_user_ids = (
            DepositIntent.objects.filter(
                completed_at__isnull=True,
                reminder_sent_at__isnull=True,
                created_at__lte=cutoff,
                created_at__gte=oldest,
            )
            .values_list("user_id", flat=True)
            .distinct()
        )

        sent = 0
        for user_id in eligible_user_ids:
            # A user may have retried the amount step more than once without
            # finishing — treat the newest abandoned attempt as the one to
            # email about, then mark every abandoned attempt of theirs as
            # reminded so retries don't each trigger their own email later.
            latest_intent = (
                DepositIntent.objects.filter(
                    user_id=user_id, completed_at__isnull=True, reminder_sent_at__isnull=True,
                )
                .select_related("user")
                .order_by("-created_at")
                .first()
            )
            if not latest_intent:
                continue

            # In-app notification goes out regardless of email deliverability —
            # it's a separate, more reliable channel. The frontend treats this
            # notif_type as a one-time popup rather than a normal feed item.
            Notification.objects.create(
                user=latest_intent.user,
                notif_type="abandoned_deposit",
                title="Complete your deposit",
                body=(
                    f"You started a deposit of ${latest_intent.amount_usd} "
                    f"({latest_intent.asset}) but didn't finish. Resume anytime from your dashboard."
                ),
            )
            email_sent = send_deposit_reminder_email(latest_intent.user, latest_intent)

            # Mark as handled either way — we've already notified in-app, so
            # there's no need to keep retrying every minute if only the email
            # failed to send.
            DepositIntent.objects.filter(
                user_id=user_id, completed_at__isnull=True, reminder_sent_at__isnull=True,
            ).update(reminder_sent_at=now)
            sent += 1
            self.stdout.write(self.style.SUCCESS(
                f"  reminded {latest_intent.user.email} "
                f"(${latest_intent.amount_usd} {latest_intent.asset})"
                + ("" if email_sent else " [email failed, in-app notification sent]")
            ))

        self.stdout.write(f"Done. {sent} reminder(s) sent.")
