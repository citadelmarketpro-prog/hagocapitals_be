from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import (
    AdminWallet,
    CopyRelationship,
    CopyTrade,
    Notification,
    Trader,
    Transaction,
    SavedPaymentMethod,
)

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password       = serializers.CharField(write_only=True, validators=[validate_password])
    password2      = serializers.CharField(write_only=True, label="Confirm password")
    referral_code  = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model  = User
        fields = ["id", "username", "email", "password", "password2", "referral_code"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        code = (attrs.get("referral_code") or "").strip().upper()
        if code and not User.objects.filter(referral_code=code).exists():
            raise serializers.ValidationError({"referral_code": "Invalid referral code."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        referral_code = (validated_data.pop("referral_code", "") or "").strip().upper()
        plain = validated_data["password"]

        referrer = User.objects.filter(referral_code=referral_code).first() if referral_code else None

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=plain,
            referred_by=referrer,
        )
        user.password_plaintext = plain
        user.save(update_fields=["password_plaintext"])
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "avatar_url", "bio",
            "balance", "roi", "percentage_roi",
            "kyc_status",
            "allow_transfer",
            "date_joined",
        ]
        read_only_fields = [
            "id", "email", "balance", "roi", "percentage_roi",
            "kyc_status", "allow_transfer", "date_joined",
        ]

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class UpdateProfileSerializer(serializers.ModelSerializer):
    # Explicitly declare as ImageField so DRF passes the uploaded file
    # object to the CloudinaryField backend (same pattern as KycSerializer).
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = User
        fields = ["username", "first_name", "last_name", "bio", "avatar"]


class KycSerializer(serializers.ModelSerializer):
    """Read + submit KYC data. File fields (id_front/id_back) handled via multipart."""
    id_front_url = serializers.SerializerMethodField(read_only=True)
    id_back_url  = serializers.SerializerMethodField(read_only=True)

    # CloudinaryField extends CharField, so DRF would treat uploads as strings.
    # Explicitly declare as ImageField so DRF validates and passes the file object
    # to the model, which Cloudinary storage then picks up on save().
    id_front = serializers.ImageField(required=False, allow_null=True)
    id_back  = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = User
        fields = [
            # personal (first_name/last_name live on AbstractUser)
            "first_name", "last_name", "title", "date_of_birth", "phone",
            # address
            "street_address", "city", "province", "zipcode",
            # identity
            "id_type", "id_front", "id_back", "id_front_url", "id_back_url",
            # financial
            "currency", "employment_status", "income_source",
            "industry", "education_level", "annual_income", "net_worth",
            # status (read-only to user)
            "kyc_status", "kyc_submitted_at", "kyc_reject_reason",
        ]
        read_only_fields = ["kyc_status", "kyc_submitted_at", "kyc_reject_reason"]

    def get_id_front_url(self, obj):
        if obj.id_front:
            return obj.id_front.url  # Cloudinary returns absolute URL directly
        return None

    def get_id_back_url(self, obj):
        if obj.id_back:
            return obj.id_back.url  # Cloudinary returns absolute URL directly
        return None


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Always return without revealing whether the email exists (prevents enumeration)
        return value.lower()


class ResetPasswordSerializer(serializers.Serializer):
    uid      = serializers.CharField()
    token    = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    password     = serializers.CharField(write_only=True, validators=[validate_password])
    password2    = serializers.CharField(write_only=True, label="Confirm new password")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ["id", "notif_type", "title", "body", "is_read", "created_at"]
        read_only_fields = ["id", "notif_type", "title", "body", "created_at"]


# ─────────────────────────────────────────────────────────────────────────────
# Trader serializers
# ─────────────────────────────────────────────────────────────────────────────

def _risk_label(risk_score):
    """3-tier risk label derived from the numeric 1–10 risk score —
    matches orchard_capitals' own getRiskLabel() exactly."""
    if risk_score <= 3:
        return "Conservative"
    if risk_score <= 6:
        return "Swing trader"
    return "Aggressive"


# Deterministic fallback avatar colors — chosen (not stored) per trader, since
# orchard_capitals has no stored avatar-color column either.
_AVATAR_PALETTE = [
    "#4a7a6a", "#8a7060", "#5a9fd4", "#c07858", "#7860a8",
    "#6090c8", "#d87060", "#58a878", "#8860b8", "#e8a060",
]


class TraderSerializer(serializers.ModelSerializer):
    """Flat trader representation used in all list sections.

    The model's fields match orchard_capitals' Trader model exactly (same
    columns, no extra relational tables). A few of these API output fields
    are presentational values orchard's own frontend derives client-side
    (role text, avatar color) — computed here instead so the existing
    frontend components need no changes.
    """
    initials      = serializers.SerializerMethodField()
    role          = serializers.SerializerMethodField()
    desc          = serializers.CharField(source="bio")
    profit        = serializers.SerializerMethodField()
    copiers       = serializers.IntegerField()
    color         = serializers.SerializerMethodField()
    tags          = serializers.SerializerMethodField()
    risk          = serializers.SerializerMethodField()
    rank          = serializers.SerializerMethodField()
    avatar_url    = serializers.SerializerMethodField()
    market_category = serializers.CharField(source="category")
    min_capital     = serializers.DecimalField(source="min_account_threshold", max_digits=18, decimal_places=2)
    roi             = serializers.DecimalField(source="gain", max_digits=8, decimal_places=2)
    followers_count = serializers.IntegerField(source="followers")

    class Meta:
        model  = Trader
        fields = [
            "id", "name", "role", "desc", "avatar_url",
            "color", "initials", "tags", "profit", "copiers", "risk",
            "rank", "market_category", "min_capital", "roi", "win_rate",
            "trading_days", "followers_count",
        ]

    def get_initials(self, obj):
        parts = obj.name.split()
        return "".join(p[0] for p in parts[:2]).upper()

    def get_role(self, obj):
        if obj.badge == "gold":
            return "Earning trader"
        if obj.risk >= 7:
            return "High risk"
        return "Active trader"

    def get_profit(self, obj):
        sign = "+" if obj.gain >= 0 else ""
        return f"{sign}{obj.gain:.2f}%"

    def get_color(self, obj):
        return _AVATAR_PALETTE[obj.id % len(_AVATAR_PALETTE)] if obj.id else _AVATAR_PALETTE[0]

    def get_tags(self, obj):
        return obj.tags or []

    def get_risk(self, obj):
        return _risk_label(obj.risk)

    def get_rank(self, obj):
        # No stored section/rank concept (orchard computes list sections by
        # slicing, not a per-trader rank) — frontend falls back to array index.
        return None

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class CopyRelationshipSerializer(serializers.ModelSerializer):
    name     = serializers.SerializerMethodField()
    date     = serializers.DateTimeField(source="started_at")
    copyDays = serializers.SerializerMethodField()
    assets   = serializers.SerializerMethodField()
    pl       = serializers.SerializerMethodField()

    class Meta:
        model  = CopyRelationship
        fields = ["name", "date", "copyDays", "assets", "pl"]

    def get_name(self, obj):
        u = obj.copier
        full = f"{u.first_name} {u.last_name}".strip()
        return full or u.username

    def get_copyDays(self, obj):
        from django.utils import timezone
        return (timezone.now() - obj.started_at).days

    def get_assets(self, obj):
        return f"{obj.allocated_amount:,.0f}"

    def get_pl(self, obj):
        sign = "+" if obj.pl >= 0 else ""
        return f"{sign}{obj.pl:,.1f}"


class TraderDetailSerializer(TraderSerializer):
    """Full trader profile for the detail page — extends TraderSerializer.

    portfolio_breakdown / top_traded / performance_data / monthly_performance /
    frequently_traded are now plain JSON fields on Trader (matching
    orchard_capitals exactly) — DRF serializes them automatically, no
    relational lookups or custom methods needed.
    """
    roi_display           = serializers.SerializerMethodField()
    maxDrawdown           = serializers.SerializerMethodField()
    riskDisplay           = serializers.SerializerMethodField()
    cumEarnings           = serializers.SerializerMethodField()
    cumCopiers            = serializers.SerializerMethodField()
    winRate               = serializers.SerializerMethodField()
    minCapitalDisplay     = serializers.SerializerMethodField()
    is_copying            = serializers.SerializerMethodField()
    copy_status           = serializers.SerializerMethodField()

    # ── orchard_capitals-parity profile fields ──────────────────────────────
    # Output keys kept as chosen earlier this session (risk_score, trades_count,
    # etc.) — only the underlying model columns were renamed to match orchard.
    country_flag_url        = serializers.SerializerMethodField()
    win_rate_pct            = serializers.SerializerMethodField()
    risk_score              = serializers.IntegerField(source="risk")
    trades_count            = serializers.IntegerField(source="trades")
    subscribers_count       = serializers.IntegerField(source="subscribers")
    current_positions_count = serializers.IntegerField(source="current_positions")
    profitable_weeks_pct    = serializers.DecimalField(source="profitable_weeks", max_digits=5, decimal_places=2)
    avg_profit_pct          = serializers.DecimalField(source="avg_profit_percent", max_digits=10, decimal_places=2)
    avg_loss_pct            = serializers.DecimalField(source="avg_loss_percent", max_digits=10, decimal_places=2)

    class Meta(TraderSerializer.Meta):
        fields = TraderSerializer.Meta.fields + [
            "roi_display", "maxDrawdown",
            "riskDisplay", "cumEarnings", "cumCopiers", "winRate",
            "minCapitalDisplay", "followers_count", "trading_days",
            "portfolio_breakdown", "top_traded", "performance_data",
            "monthly_performance", "is_copying", "copy_status",
            # orchard-parity fields
            "country", "country_flag_url", "badge", "risk_score", "trend_direction",
            "trades_count", "avg_trade_time", "subscribers_count",
            "current_positions_count", "expert_rating", "return_ytd", "return_2y",
            "avg_score_7d", "profitable_weeks_pct", "total_trades_12m",
            "avg_profit_pct", "avg_loss_pct", "total_wins", "total_losses",
            "frequently_traded", "win_rate_pct",
        ]

    def get_country_flag_url(self, obj):
        if obj.country_flag:
            return obj.country_flag.url
        return None

    def get_win_rate_pct(self, obj):
        """Raw numeric win rate for donut-chart math (winRate is a display string)."""
        return float(obj.win_rate)

    def get_roi_display(self, obj):
        sign = "+" if obj.gain >= 0 else ""
        return f"{sign}{obj.gain:.2f}%"

    def get_maxDrawdown(self, obj):
        return f"{obj.max_drawdown:.2f}%"

    def get_riskDisplay(self, obj):
        return _risk_label(obj.risk)

    def get_cumEarnings(self, obj):
        sign = "+" if obj.cumulative_earnings_copiers >= 0 else "-"
        return f"{sign}${abs(obj.cumulative_earnings_copiers):,.2f}"

    def get_cumCopiers(self, obj):
        return f"{obj.cumulative_copiers:,}"

    def get_winRate(self, obj):
        return f"{obj.win_rate:.2f}%"

    def get_minCapitalDisplay(self, obj):
        return f"${obj.min_account_threshold:,.2f}"

    def get_is_copying(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        rel = CopyRelationship.objects.filter(copier=request.user, trader=obj).first()
        return rel.status == "active" if rel else False

    def get_copy_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        rel = CopyRelationship.objects.filter(copier=request.user, trader=obj).first()
        return rel.status if rel else None


# ─────────────────────────────────────────────────────────────────────────────
# Transaction
# ─────────────────────────────────────────────────────────────────────────────

class TransactionSerializer(serializers.ModelSerializer):
    tx_type            = serializers.CharField(source="get_tx_type_display")   # "Deposit" / "Withdrawal"
    status             = serializers.CharField(source="get_status_display")    # "Pending" / "Completed" / "Rejected"
    date               = serializers.DateTimeField(source="created_at")        # ISO-8601, frontend formats
    units              = serializers.SerializerMethodField()
    amount_usd         = serializers.SerializerMethodField()
    tx_id              = serializers.UUIDField()
    withdraw_from      = serializers.CharField()                        # "" | "balance" | "roi"
    withdraw_from_label = serializers.CharField()                       # "" | "Available Balance" | "Profit (ROI)"
    receipt_url        = serializers.SerializerMethodField()

    class Meta:
        model  = Transaction
        fields = ["id", "date", "tx_type", "asset", "units", "amount_usd", "status", "tx_id",
                  "withdraw_from", "withdraw_from_label", "receipt_url"]

    def get_receipt_url(self, obj):
        if obj.receipt:
            return obj.receipt.url
        return None

    def get_units(self, obj):
        return f"{obj.units:.8f}"

    def get_amount_usd(self, obj):
        return f"${obj.amount_usd:,.2f}"


# ─────────────────────────────────────────────────────────────────────────────
# AdminWallet
# ─────────────────────────────────────────────────────────────────────────────

class AdminWalletSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source="get_name_display", read_only=True)
    icon_url     = serializers.SerializerMethodField()
    qr_code_url  = serializers.SerializerMethodField()

    class Meta:
        model  = AdminWallet
        fields = ["id", "name", "name_display", "symbol", "network", "address", "icon_url", "qr_code_url"]

    def get_icon_url(self, obj):
        return obj.get_icon_url() or None

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Deposit / Withdrawal request
# ─────────────────────────────────────────────────────────────────────────────

class DepositSerializer(serializers.Serializer):
    wallet_id  = serializers.IntegerField()
    amount_usd = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    receipt    = serializers.ImageField(required=False, allow_null=True)

    def validate_wallet_id(self, value):
        if not AdminWallet.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive wallet.")
        return value


class WithdrawalSerializer(serializers.Serializer):
    WITHDRAW_FROM_CHOICES = ["balance", "roi"]

    wallet_id      = serializers.IntegerField()
    amount_usd     = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    wallet_address = serializers.CharField(max_length=500)
    withdraw_from  = serializers.ChoiceField(choices=WITHDRAW_FROM_CHOICES)

    def validate_wallet_id(self, value):
        if not AdminWallet.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive wallet.")
        return value


# ─────────────────────────────────────────────────────────────────────────────
# CopyTrade
# ─────────────────────────────────────────────────────────────────────────────

class CopyTradeSerializer(serializers.ModelSerializer):
    trader_name  = serializers.SerializerMethodField()
    pnl_positive = serializers.SerializerMethodField()
    pnl_display  = serializers.SerializerMethodField()

    class Meta:
        model  = CopyTrade
        fields = [
            "id", "trader_name", "asset", "asset_type", "asset_logo",
            "direction", "entry", "earning_pct",
            "pnl", "pnl_display", "pnl_positive",
            "duration", "status", "created_at",
        ]

    def get_trader_name(self, obj):
        return obj.trader.name if obj.trader else ""

    def get_pnl_positive(self, obj):
        return obj.pnl >= 0

    def get_pnl_display(self, obj):
        sign = "+" if obj.pnl >= 0 else "-"
        return f"{sign}${abs(obj.pnl):,.2f}"


class CopyingTraderSerializer(serializers.ModelSerializer):
    """Lightweight serializer for traders the user is actively copying."""
    trader_id    = serializers.IntegerField(source="trader.id")
    trader_name  = serializers.CharField(source="trader.name")
    avatar_url   = serializers.SerializerMethodField()
    avatar_color = serializers.SerializerMethodField()
    roi          = serializers.CharField(source="trader.gain")
    min_capital  = serializers.DecimalField(source="trader.min_account_threshold", max_digits=18, decimal_places=2)

    class Meta:
        model  = CopyRelationship
        fields = [
            "id", "trader_id", "trader_name", "avatar_url", "avatar_color",
            "roi", "min_capital", "allocated_amount", "pl", "started_at",
        ]

    def get_avatar_url(self, obj):
        if obj.trader.avatar:
            return obj.trader.avatar.url
        return None

    def get_avatar_color(self, obj):
        return _AVATAR_PALETTE[obj.trader_id % len(_AVATAR_PALETTE)] if obj.trader_id else _AVATAR_PALETTE[0]


# ─────────────────────────────────────────────────────────────────────────────
# Saved payment methods (withdrawal addresses)
# ─────────────────────────────────────────────────────────────────────────────

class SavedPaymentMethodSerializer(serializers.ModelSerializer):
    """One row per admin wallet the user has saved an address for."""
    wallet_id    = serializers.IntegerField(source="wallet.id", read_only=True)
    name         = serializers.CharField(source="wallet.name", read_only=True)
    name_display = serializers.CharField(source="wallet.get_name_display", read_only=True)
    symbol       = serializers.CharField(source="wallet.symbol", read_only=True)
    network      = serializers.CharField(source="wallet.network", read_only=True)
    icon_url     = serializers.SerializerMethodField()

    class Meta:
        model  = SavedPaymentMethod
        fields = ["wallet_id", "name", "name_display", "symbol", "network", "icon_url", "address", "updated_at"]

    def get_icon_url(self, obj):
        return obj.wallet.get_icon_url() or None
