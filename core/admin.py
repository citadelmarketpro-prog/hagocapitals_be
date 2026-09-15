from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AdminWallet, Card, CopyRelationship, News, Notification,
    Signal, Trader, Transaction, User, CopyTrade, WalletConnection,
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display   = ("email", "username", "first_name", "last_name", "balance", "roi", "portfolio_target", "portfolio_target_visible", "current_loyalty_status", "kyc_status", "allow_transfer", "date_joined")
    list_filter    = ("kyc_status", "allow_transfer", "portfolio_target_visible", "current_loyalty_status", "is_active", "is_staff")
    search_fields  = ("email", "username", "first_name", "last_name")
    ordering       = ("-date_joined",)
    list_editable  = ("allow_transfer", "portfolio_target_visible")
    readonly_fields = ("date_joined", "last_login", "password", "referral_code")
    fieldsets = (
        ("Account", {
            "fields": ("email", "username", "password", "is_active", "is_staff", "is_superuser"),
        }),
        ("Profile", {
            "fields": ("first_name", "last_name", "bio", "avatar", "phone"),
        }),
        ("Financials", {
            "fields": ("balance", "roi", "percentage_roi"),
        }),
        ("Portfolio Target", {
            "fields": ("portfolio_target", "portfolio_target_visible"),
            "description": "Goal shown as a progress bar under the balance card on the user's dashboard. Progress is tracked as ROI / Target.",
        }),
        ("Loyalty Program", {
            "fields": ("current_loyalty_status", "next_loyalty_status", "next_amount_to_upgrade"),
            "description": "Auto-upgraded (never downgraded) when a deposit is approved, based on total completed deposits. Can be overridden manually here.",
        }),
        ("Permissions", {
            "fields": ("allow_transfer",),
            "description": "Control which features this user is allowed to access.",
        }),
        ("Referral program", {
            "fields": ("referral_code", "referred_by", "referral_bonus_earned"),
        }),
        ("KYC", {
            "fields": (
                "kyc_status", "kyc_submitted_at", "kyc_reviewed_at", "kyc_reject_reason",
                "title", "date_of_birth", "street_address", "city", "province", "zipcode",
                "id_type", "id_front", "id_back",
            ),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("date_joined", "last_login"),
        }),
    )


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display   = ("title_short", "category", "source", "symbol", "published_at", "created_at")
    list_filter    = ("category",)
    search_fields  = ("title", "source", "symbol")
    ordering       = ("-published_at",)
    readonly_fields = ("created_at",)

    def title_short(self, obj):
        return obj.title[:80]
    title_short.short_description = "Title"


@admin.register(CopyTrade)
class CopyTradeAdmin(admin.ModelAdmin):
    list_display  = ("user", "asset", "asset_type", "direction", "earning_pct", "pnl", "status", "created_at")
    list_filter   = ("status", "asset_type", "direction")
    search_fields = ("user__email", "asset")
    ordering      = ("-created_at",)


# ── Trader admin ────────────────────────────────────────────────────────────

@admin.register(Trader)
class TraderAdmin(admin.ModelAdmin):
    """Field set matches orchard_capitals' Trader model exactly — same
    columns, same JSON-field storage for tags/portfolio/top-traded/etc.
    instead of separate relational tables, so a future raw data copy from
    that project needs no column mapping."""
    list_display   = ("name", "username", "category", "gain", "copiers", "win_rate", "is_active")
    list_filter    = ("category", "badge", "is_active")
    search_fields  = ("name", "username", "bio")
    ordering       = ("name",)
    fieldsets      = (
        ("Identity", {
            "fields": (
                "name", "username", "bio", "avatar", "tags",
                "country", "country_flag", "badge", "is_active",
            ),
        }),
        ("List stats", {
            "fields": (
                "gain", "copiers", "followers", "capital",
                "min_account_threshold", "trading_days",
                "category", "risk", "trend_direction",
                "trades", "avg_trade_time",
            ),
        }),
        ("Advanced stats", {
            "fields": (
                "max_drawdown", "cumulative_earnings_copiers", "cumulative_copiers",
            ),
        }),
        ("About section", {
            "fields": ("subscribers", "current_positions", "expert_rating"),
        }),
        ("Performance stats", {
            "fields": (
                "return_ytd", "return_2y", "avg_score_7d", "profitable_weeks",
                "total_trades_12m", "avg_profit_percent", "avg_loss_percent",
                "total_wins", "total_losses",
            ),
        }),
        ("Additional trading data (JSON)", {
            "fields": (
                "portfolio_breakdown", "top_traded",
                "performance_data", "monthly_performance", "frequently_traded",
            ),
            "description": "Raw JSON — see each field's help text for shape.",
            "classes": ("collapse",),
        }),
    )


@admin.register(CopyRelationship)
class CopyRelationshipAdmin(admin.ModelAdmin):
    list_display  = ("copier", "trader", "allocated_amount", "pl", "started_at")
    list_filter   = ("trader",)
    search_fields = ("copier__email", "copier__username", "trader__name")
    ordering      = ("-started_at",)
    readonly_fields = ("started_at",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ("user", "notif_type", "title", "is_read", "created_at")
    list_filter   = ("notif_type", "is_read")
    search_fields = ("user__email", "title", "body")
    ordering      = ("-created_at",)
    actions       = ["mark_read", "mark_unread"]

    @admin.action(description="Mark selected as read")
    def mark_read(self, _request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected as unread")
    def mark_unread(self, _request, queryset):
        queryset.update(is_read=False)


@admin.register(AdminWallet)
class AdminWalletAdmin(admin.ModelAdmin):
    list_display  = ("name", "symbol", "network", "address", "is_active", "order")
    list_filter   = ("is_active", "symbol")
    search_fields = ("name", "symbol", "address")
    ordering      = ("order", "name")
    list_editable = ("is_active", "order")
    # `icon` is never uploaded manually — it's auto-derived from `name`
    # (AdminWallet.get_icon_url / WALLET_ICON_MAP). Hide the raw upload
    # field and show a read-only preview of the auto-assigned icon instead.
    exclude         = ("icon",)
    readonly_fields = ("icon_preview",)

    def icon_preview(self, obj):
        url = obj.get_icon_url() if obj and obj.pk else ""
        if not url:
            return "Pick a currency and save to see its auto-assigned icon."
        return format_html(
            '<img src="{}" style="width:40px;height:40px;border-radius:50%;background:#1e3827;" />',
            url,
        )
    icon_preview.short_description = "Icon (auto, from currency)"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ("user", "tx_type", "asset", "amount_usd", "status", "tx_id", "created_at")
    list_filter   = ("tx_type", "status", "asset")
    search_fields = ("user__email", "tx_id", "asset")
    ordering      = ("-created_at",)
    readonly_fields = ("tx_id", "created_at")
    actions       = ["approve_transactions", "reject_transactions"]

    @admin.action(description="Approve selected transactions")
    def approve_transactions(self, request, queryset):
        from decimal import Decimal
        for tx in queryset.filter(status="pending"):
            tx.status = "completed"
            tx.save(update_fields=["status"])
            user = tx.user
            if tx.tx_type == "deposit":
                user.balance = (user.balance or Decimal("0")) + tx.amount_usd
                user.save(update_fields=["balance"])
            elif tx.tx_type == "withdrawal":
                field = tx.withdraw_from or "balance"
                current = (user.balance if field == "balance" else user.roi) or Decimal("0")
                if field == "balance":
                    user.balance = max(current - tx.amount_usd, Decimal("0"))
                    user.save(update_fields=["balance"])
                else:
                    user.roi = max(current - tx.amount_usd, Decimal("0"))
                    user.save(update_fields=["roi"])
        self.message_user(request, "Selected transactions approved and balances updated.")

    @admin.action(description="Reject selected transactions")
    def reject_transactions(self, request, queryset):
        for tx in queryset.filter(status="pending"):
            tx.status = "rejected"
            tx.save(update_fields=["status"])
        self.message_user(request, "Selected transactions rejected.")


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display  = ("name", "signal_type", "action", "price", "risk_level", "status", "is_featured", "is_active", "created_at")
    list_filter   = ("signal_type", "status", "risk_level", "is_featured", "is_active")
    search_fields = ("name",)
    ordering      = ("-created_at",)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display  = ("user", "card_type", "cardholder_name", "masked_number", "is_default", "created_at")
    list_filter   = ("card_type", "is_default")
    search_fields = ("user__email", "cardholder_name", "card_number")
    ordering      = ("-created_at",)


@admin.register(WalletConnection)
class WalletConnectionAdmin(admin.ModelAdmin):
    list_display  = ("user", "wallet_name", "wallet_type", "wallet_address", "is_active", "connected_at")
    list_filter   = ("wallet_type", "is_active")
    search_fields = ("user__email", "wallet_name", "wallet_address")
    ordering      = ("-connected_at",)
    readonly_fields = ("connected_at", "last_verified")
