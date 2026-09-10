"""
Reconcile every user's loyalty tier against their real total completed
deposits — for backfilling existing accounts after the Loyalty Program
feature was added, or after manually editing deposit records.

Only ever upgrades (matches User.update_loyalty_tier()'s own rule), credits
the rank-bonus difference to balance, and creates the same upgrade
Notification a live deposit-approval would. Dry-run by default.

Usage:
    python manage.py sync_loyalty_tiers            # preview only
    python manage.py sync_loyalty_tiers --apply     # actually write changes
"""

from django.core.management.base import BaseCommand

from core.models import User


class Command(BaseCommand):
    help = "Recompute every user's loyalty tier from their total completed deposits."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true",
            help="Actually apply upgrades. Without this flag, only prints what would change.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        upgraded = 0
        checked = 0

        for user in User.objects.all():
            checked += 1
            before = user.current_loyalty_status

            if apply_changes:
                changed = user.update_loyalty_tier()
                if changed:
                    upgraded += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"  {user.email}: {before} -> {user.current_loyalty_status}"
                    ))
            else:
                # Dry-run: mirror update_loyalty_tier()'s tier lookup without saving.
                from decimal import Decimal
                from django.db.models import Sum
                from core.models import Transaction

                total_deposits = Transaction.objects.filter(
                    user=user, tx_type="deposit", status="completed",
                ).aggregate(total=Sum("amount_usd"))["total"] or Decimal("0")

                new_tier = "iron"
                for tier_key in User.LOYALTY_TIER_ORDER:
                    if total_deposits >= User.LOYALTY_TIER_CONFIG[tier_key]["min_deposit"]:
                        new_tier = tier_key

                old_index = User.LOYALTY_TIER_ORDER.index(before) if before in User.LOYALTY_TIER_ORDER else 0
                new_index = User.LOYALTY_TIER_ORDER.index(new_tier)
                if new_index > old_index:
                    upgraded += 1
                    self.stdout.write(f"  {user.email}: {before} -> {new_tier} (total deposits: ${total_deposits:,.2f})")

        self.stdout.write("")
        if apply_changes:
            self.stdout.write(self.style.SUCCESS(
                f"Done. Checked {checked} user(s), upgraded {upgraded}."
            ))
        else:
            self.stdout.write(
                f"Dry run. Checked {checked} user(s), {upgraded} would be upgraded. "
                f"Re-run with --apply to write changes."
            )
