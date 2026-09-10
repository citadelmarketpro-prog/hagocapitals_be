import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


class User(AbstractUser):
    """
    Extended user model for HagoCapitals.
    Username + email are both required and unique.
    """
    email = models.EmailField(unique=True)

    # Profile
    avatar = CloudinaryField("avatar", folder="avatars", null=True, blank=True)
    bio    = models.TextField(blank=True, default="")

    # Financials (stored in USD)
    balance        = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    roi            = models.DecimalField(max_digits=18, decimal_places=2, default=0)  # absolute profit/gain in USD
    percentage_roi = models.DecimalField(max_digits=8,  decimal_places=2, default=0)  # cumulative % across all trades

    # Portfolio Target — admin-set goal shown as a progress bar under the
    # balance card on the user's dashboard. Progress is profit (roi) / target.
    portfolio_target = models.DecimalField(
        max_digits=20, decimal_places=2, default=50000, null=True, blank=True,
        help_text="Admin-set portfolio target shown as a progress bar on the user's dashboard.",
    )
    portfolio_target_visible = models.BooleanField(
        default=False,
        help_text="Show the Portfolio Target progress bar on the user's dashboard.",
    )

    # ── Loyalty Program ──────────────────────────────────────────────────────
    # Tier is admin-overridable (see UserEditForm / Django admin) but also
    # auto-computed via update_loyalty_tier() whenever a deposit is approved
    # — see dashboard.views.transaction_approve. Never downgrades.
    LOYALTY_TIERS = [
        ("iron",     "Iron"),
        ("bronze",   "Bronze"),
        ("silver",   "Silver"),
        ("gold",     "Gold"),
        ("platinum", "Platinum"),
        ("diamond",  "Diamond"),
        ("elite",    "Elite"),
    ]
    LOYALTY_TIER_ORDER = ["iron", "bronze", "silver", "gold", "platinum", "diamond", "elite"]
    LOYALTY_TIER_CONFIG = {
        "iron":     {"min_deposit": 2500,    "referral_bonus": 5,  "rank_bonus": 0},
        "bronze":   {"min_deposit": 5000,    "referral_bonus": 5,  "rank_bonus": 50},
        "silver":   {"min_deposit": 25000,   "referral_bonus": 10, "rank_bonus": 250},
        "gold":     {"min_deposit": 100000,  "referral_bonus": 10, "rank_bonus": 1000},
        "platinum": {"min_deposit": 250000,  "referral_bonus": 12, "rank_bonus": 2500},
        "diamond":  {"min_deposit": 500000,  "referral_bonus": 12, "rank_bonus": 5000},
        "elite":    {"min_deposit": 1000000, "referral_bonus": 15, "rank_bonus": 10000},
    }

    current_loyalty_status = models.CharField(
        max_length=20, choices=LOYALTY_TIERS, default="iron",
        help_text="Current loyalty tier.",
    )
    next_loyalty_status = models.CharField(
        max_length=20, choices=LOYALTY_TIERS, default="bronze",
        help_text="Next loyalty tier.",
    )
    next_amount_to_upgrade = models.DecimalField(
        max_digits=20, decimal_places=2, default=5000,
        help_text="Total completed deposits required to reach the next loyalty tier.",
    )

    def update_loyalty_tier(self):
        """Check total completed deposits and upgrade the loyalty tier if
        eligible. Credits the rank-bonus difference to balance on upgrade.
        Only ever upgrades — never downgrades. Returns True if an upgrade
        occurred. Call this after a deposit Transaction is marked completed."""
        from decimal import Decimal
        from django.db.models import Sum

        total_deposits = Transaction.objects.filter(
            user=self, tx_type="deposit", status="completed",
        ).aggregate(total=Sum("amount_usd"))["total"] or Decimal("0")

        new_tier = "iron"
        for tier_key in self.LOYALTY_TIER_ORDER:
            if total_deposits >= self.LOYALTY_TIER_CONFIG[tier_key]["min_deposit"]:
                new_tier = tier_key

        old_tier = self.current_loyalty_status
        old_index = self.LOYALTY_TIER_ORDER.index(old_tier) if old_tier in self.LOYALTY_TIER_ORDER else 0
        new_index = self.LOYALTY_TIER_ORDER.index(new_tier)
        if new_index <= old_index:
            return False

        old_rank_bonus = Decimal(str(self.LOYALTY_TIER_CONFIG.get(old_tier, {}).get("rank_bonus", 0)))
        new_rank_bonus = Decimal(str(self.LOYALTY_TIER_CONFIG[new_tier]["rank_bonus"]))
        bonus_credit = new_rank_bonus - old_rank_bonus

        self.current_loyalty_status = new_tier
        if new_index < len(self.LOYALTY_TIER_ORDER) - 1:
            next_tier = self.LOYALTY_TIER_ORDER[new_index + 1]
            self.next_loyalty_status = next_tier
            self.next_amount_to_upgrade = Decimal(str(self.LOYALTY_TIER_CONFIG[next_tier]["min_deposit"]))
        else:
            self.next_loyalty_status = new_tier
            self.next_amount_to_upgrade = Decimal("0")

        if bonus_credit > 0:
            self.balance += bonus_credit

        self.save(update_fields=["current_loyalty_status", "next_loyalty_status", "next_amount_to_upgrade", "balance"])

        Notification.objects.create(
            user=self,
            notif_type="system",
            title="Loyalty Rank Upgraded!",
            body=(
                f"Congratulations! You have been upgraded to {new_tier.capitalize()} tier. "
                f"Rank bonus credited: ${bonus_credit:.2f}."
            ),
        )
        return True

    # ── KYC — Personal ───────────────────────────────────────────────────────
    title         = models.CharField(max_length=10,  blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    phone         = models.CharField(max_length=30,  blank=True, default="")

    # ── KYC — Address ────────────────────────────────────────────────────────
    street_address = models.CharField(max_length=255, blank=True, default="")
    city           = models.CharField(max_length=100, blank=True, default="")
    province       = models.CharField(max_length=100, blank=True, default="")
    zipcode        = models.CharField(max_length=20,  blank=True, default="")

    # ── KYC — Identity documents ─────────────────────────────────────────────
    ID_TYPE_CHOICES = [
        ("passport",         "Passport"),
        ("national_id",      "National ID"),
        ("drivers_license",  "Driver's Licence"),
        ("residence_permit", "Residence Permit"),
    ]
    id_type  = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, blank=True, default="")
    id_front = CloudinaryField("id_front", folder="kyc/id", null=True, blank=True)
    id_back  = CloudinaryField("id_back",  folder="kyc/id", null=True, blank=True)

    # ── KYC — Financial background ────────────────────────────────────────────
    currency          = models.CharField(max_length=10,  blank=True, default="")
    employment_status = models.CharField(max_length=60,  blank=True, default="")
    income_source     = models.CharField(max_length=100, blank=True, default="")
    industry          = models.CharField(max_length=100, blank=True, default="")
    education_level   = models.CharField(max_length=60,  blank=True, default="")
    annual_income     = models.CharField(max_length=60,  blank=True, default="")
    net_worth         = models.CharField(max_length=60,  blank=True, default="")

    # ── KYC — Status ─────────────────────────────────────────────────────────
    KYC_STATUS_CHOICES = [
        ("not_submitted", "Not submitted"),
        ("submitted",     "Submitted"),
        ("under_review",  "Under review"),
        ("approved",      "Approved"),
        ("rejected",      "Rejected"),
    ]
    kyc_status        = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default="not_submitted")
    kyc_submitted_at  = models.DateTimeField(null=True, blank=True)
    kyc_reviewed_at   = models.DateTimeField(null=True, blank=True)
    kyc_reject_reason = models.TextField(blank=True, default="")

    # ── Permissions ──────────────────────────────────────────────────────────
    allow_transfer = models.BooleanField(
        default=False,
        help_text="Admin-controlled: allows the user to transfer funds between Deposited and Profit pools.",
    )

    # ── Referral program ─────────────────────────────────────────────────────
    referral_code = models.CharField(
        max_length=12, unique=True, blank=True, null=True,
        help_text="User's unique referral code",
    )
    referred_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="referrals",
        help_text="User who referred this person",
    )
    referral_bonus_earned = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="Total bonus earned from referrals",
    )

    # Dev-only: plain-text copy of the password (never use in production auth)
    password_plaintext = models.CharField(max_length=255, blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


# ─────────────────────────────────────────────────────────────────────────────
# Notification
# ─────────────────────────────────────────────────────────────────────────────

class Notification(models.Model):
    TYPE_CHOICES = [
        ("trade",  "Trade"),
        ("wallet", "Wallet"),
        ("news",   "News"),
        ("kyc",    "KYC"),
        ("system", "System"),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="system")
    title      = models.CharField(max_length=255)
    body       = models.TextField(blank=True, default="")
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.title}"


# ─────────────────────────────────────────────────────────────────────────────
# Trader — Tags
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Trader — standalone profile (independent of User accounts)
# Field set matches orchard_capitals' Trader model exactly — same column
# names, same JSON-field storage for the list-style data (tags, portfolio
# breakdown, top traded assets, etc.) instead of separate relational tables.
# ─────────────────────────────────────────────────────────────────────────────

class Trader(models.Model):
    BADGE_CHOICES = [
        ("gold",   "Gold"),
        ("silver", "Silver"),
        ("bronze", "Bronze"),
    ]
    TREND_CHOICES = [
        ("upward",   "Upward"),
        ("downward", "Downward"),
    ]
    MARKET_CATEGORY_CHOICES = [
        ("crypto",             "Crypto"),
        ("stocks",             "Stocks"),
        ("healthcare",         "Healthcare"),
        ("financial_services", "Financial Services"),
        ("options",            "Options"),
        ("tech",               "Tech"),
        ("etf",                "ETF"),
        ("manufacturing",      "Manufacturing"),
    ]
    AVG_TRADE_TIME_CHOICES = [
        ("1 day",    "1 Day"),
        ("3 days",   "3 Days"),
        ("1 week",   "1 Week"),
        ("2 weeks",  "2 Weeks"),
        ("3 weeks",  "3 Weeks"),
        ("1 month",  "1 Month"),
        ("2 months", "2 Months"),
        ("3 months", "3 Months"),
        ("6 months", "6 Months"),
    ]

    # Identity
    name         = models.CharField(max_length=200)
    username     = models.CharField(max_length=100, unique=True, null=True, blank=True, help_text="e.g. '@kristijan'.")
    bio          = models.TextField(blank=True, default="")
    avatar       = CloudinaryField("avatar", folder="trader_avatars", null=True, blank=True)
    country          = models.CharField(max_length=100, blank=True, default="")
    country_flag     = CloudinaryField("country flag", folder="trader_flags", null=True, blank=True)
    badge            = models.CharField(max_length=10, choices=BADGE_CHOICES, default="bronze")
    is_active        = models.BooleanField(default=True, help_text="Is this trader available for copying?")

    # Trading info
    gain          = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Overall gain, %.")
    risk          = models.PositiveSmallIntegerField(default=5, help_text="Risk score from 1 (conservative) to 10 (aggressive).")
    capital       = models.CharField(max_length=50, blank=True, default="", help_text="Capital under management, e.g. '50000'.")
    copiers       = models.PositiveIntegerField(default=0)
    avg_trade_time = models.CharField(max_length=50, choices=AVG_TRADE_TIME_CHOICES, blank=True, default="")
    trades        = models.PositiveIntegerField(default=0, help_text="Total number of trades this trader has taken.")

    # Stats fields
    subscribers        = models.PositiveIntegerField(default=0)
    current_positions   = models.PositiveIntegerField(default=0)
    min_account_threshold = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    expert_rating      = models.DecimalField(max_digits=3, decimal_places=2, default=5.00, help_text="Rating out of 5.00.")

    # Performance stats
    return_ytd         = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Return Year To Date, %.")
    return_2y          = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Return over 2 years, %.")
    avg_score_7d       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profitable_weeks   = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Trading stats
    total_trades_12m   = models.PositiveIntegerField(default=0)
    avg_profit_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_loss_percent   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_wins         = models.PositiveIntegerField(default=0)
    total_losses       = models.PositiveIntegerField(default=0)

    # Profile & display
    followers        = models.PositiveIntegerField(default=0)
    trading_days     = models.PositiveIntegerField(default=0)
    trend_direction  = models.CharField(max_length=10, choices=TREND_CHOICES, default="upward")
    tags             = models.JSONField(default=list, blank=True, help_text='Badge tags, e.g. ["Trending Investors", "Rising Stars"]')
    category         = models.CharField(max_length=30, choices=MARKET_CATEGORY_CHOICES, blank=True, default="")

    # Advanced stats
    max_drawdown   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cumulative_earnings_copiers = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cumulative_copiers          = models.PositiveIntegerField(default=0)

    # Portfolio breakdown
    portfolio_breakdown = models.JSONField(
        default=list, blank=True,
        help_text='e.g. [{"name": "ETF", "percentage": 25}, {"name": "Crypto", "percentage": 75}]',
    )

    # Top traded assets with detailed stats
    top_traded = models.JSONField(
        default=list, blank=True,
        help_text='e.g. [{"name": "Apple Inc", "ticker": "AAPL", "avg_profit": 12.5, "avg_loss": -3.2, "profitable_pct": 78}]',
    )

    # JSON fields for complex data
    performance_data    = models.JSONField(default=list, blank=True, help_text="Monthly performance data as list of {month, value}.")
    monthly_performance = models.JSONField(default=list, blank=True, help_text="Monthly performance percentages as list of {month, percentage}.")
    frequently_traded   = models.JSONField(default=list, blank=True, help_text="List of frequently traded asset tickers.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-gain", "-copiers"]

    def __str__(self):
        return self.name

    @property
    def win_rate(self):
        """Win rate percentage, derived — matches orchard_capitals (not stored)."""
        total = self.total_wins + self.total_losses
        if total == 0:
            return 0
        return (self.total_wins / total) * 100


# ─────────────────────────────────────────────────────────────────────────────
# Trader — Copy relationship (copiers tab)
# copier = a regular User; trader = a Trader profile
# ─────────────────────────────────────────────────────────────────────────────

class CopyRelationship(models.Model):
    STATUS_CHOICES = [
        ("active",           "Active"),
        ("cancel_requested", "Cancel Requested"),
        ("cancelled",        "Cancelled"),
    ]

    copier           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="copying")
    trader           = models.ForeignKey("Trader", on_delete=models.CASCADE, related_name="copiers_rel")
    started_at       = models.DateTimeField(auto_now_add=True)
    allocated_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    pl               = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        unique_together = [("copier", "trader")]
        ordering        = ["-started_at"]

    def __str__(self):
        return f"{self.copier} copies {self.trader} [{self.status}]"


# ─────────────────────────────────────────────────────────────────────────────
# Copy Trade — individual trade injected by admin for a copy relationship
# ─────────────────────────────────────────────────────────────────────────────

class CopyTrade(models.Model):
    DIRECTION_CHOICES = [("Buy", "Buy"), ("Sell", "Sell")]
    STATUS_CHOICES    = [("open", "Open"), ("closed", "Closed"), ("pending", "Pending")]
    TYPE_CHOICES      = [
        ("stock",  "Stock"),
        ("crypto", "Crypto"),
        ("forex",  "Forex"),
    ]
    DURATION_CHOICES  = [
        ("2m",  "2 Minutes"),
        ("5m",  "5 Minutes"),
        ("10m", "10 Minutes"),
        ("15m", "15 Minutes"),
        ("30m", "30 Minutes"),
        ("1h",  "1 Hour"),
        ("2h",  "2 Hours"),
        ("4h",  "4 Hours"),
        ("6h",  "6 Hours"),
        ("12h", "12 Hours"),
        ("1d",  "1 Day"),
        ("3d",  "3 Days"),
        ("1w",  "1 Week"),
    ]

    copy_relationship = models.ForeignKey("CopyRelationship", on_delete=models.SET_NULL, null=True, blank=True, related_name="trades")
    user              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="copy_trades")
    trader            = models.ForeignKey("Trader", on_delete=models.SET_NULL, null=True, blank=True, related_name="investor_trades")
    asset             = models.CharField(max_length=100)
    asset_type        = models.CharField(max_length=10, choices=TYPE_CHOICES, default="stock")
    asset_logo        = models.URLField(max_length=500, blank=True, default="")
    direction         = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default="Buy")
    entry             = models.DecimalField(max_digits=18, decimal_places=2, default=0)   # entry price
    earning_pct       = models.DecimalField(max_digits=8,  decimal_places=2, default=0)   # % entered by admin
    pnl               = models.DecimalField(max_digits=18, decimal_places=2, default=0)   # calculated USD value
    duration          = models.CharField(max_length=10, choices=DURATION_CHOICES, default="1h")
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} | {self.asset} {self.direction} {self.earning_pct}%"


# ─────────────────────────────────────────────────────────────────────────────
# Transaction (deposit / withdrawal)
# ─────────────────────────────────────────────────────────────────────────────

class Transaction(models.Model):
    TX_TYPE_CHOICES = [
        ("deposit",    "Deposit"),
        ("withdrawal", "Withdrawal"),
    ]
    STATUS_CHOICES = [
        ("pending",   "Pending"),
        ("completed", "Completed"),
        ("rejected",  "Rejected"),
    ]

    user           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    tx_type        = models.CharField(max_length=20, choices=TX_TYPE_CHOICES)
    asset          = models.CharField(max_length=20)
    units          = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    amount_usd     = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    wallet_address = models.CharField(max_length=500, blank=True, default="")
    withdraw_from  = models.CharField(max_length=10, blank=True, default="")  # "balance" | "roi" — set on withdrawals
    receipt        = CloudinaryField("receipt", folder="deposit_receipts", null=True, blank=True)  # deposit payment proof
    tx_id          = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.tx_type} {self.asset} ({self.status})"

    @property
    def withdraw_from_label(self) -> str:
        """Human-readable withdrawal source — empty for deposits, or for
        withdrawals predating this field (those defaulted to "balance" when
        approved, but we don't retroactively claim a source wasn't recorded)."""
        if self.tx_type != "withdrawal" or not self.withdraw_from:
            return ""
        return "Profit (ROI)" if self.withdraw_from == "roi" else "Available Balance"


# ─────────────────────────────────────────────────────────────────────────────
# AdminWallet — deposit addresses managed by the admin
# ─────────────────────────────────────────────────────────────────────────────

class AdminWallet(models.Model):
    WALLET_TYPE_CHOICES = [
        ("bitcoin",       "Bitcoin"),
        ("ethereum",      "Ethereum"),
        ("usdt_trc20",    "USDT (TRC20)"),
        ("usdt_erc20",    "USDT (ERC20)"),
        ("bnb",           "BNB (BEP20)"),
        ("usdc",          "USDC"),
        ("litecoin",      "Litecoin"),
        ("ripple",        "Ripple (XRP)"),
        ("solana",        "Solana"),
        ("dogecoin",      "Dogecoin"),
        ("tron",          "Tron (TRX)"),
        ("polygon",       "Polygon (MATIC)"),
        ("avalanche",     "Avalanche (AVAX)"),
        ("bitcoin_cash",  "Bitcoin Cash"),
    ]

    WALLET_DEFAULTS = {
        "bitcoin":       ("BTC",  "Bitcoin"),
        "ethereum":      ("ETH",  "ERC20"),
        "usdt_trc20":    ("USDT", "TRC20"),
        "usdt_erc20":    ("USDT", "ERC20"),
        "bnb":           ("BNB",  "BEP20"),
        "usdc":          ("USDC", "ERC20"),
        "litecoin":      ("LTC",  "Litecoin"),
        "ripple":        ("XRP",  "Ripple"),
        "solana":        ("SOL",  "Solana"),
        "dogecoin":      ("DOGE", "Dogecoin"),
        "tron":          ("TRX",  "TRC20"),
        "polygon":       ("MATIC","Polygon"),
        "avalanche":     ("AVAX", "C-Chain"),
        "bitcoin_cash":  ("BCH",  "Bitcoin Cash"),
    }

    # Real-brand coin logos, keyed by `name` — auto-applied so admins never
    # have to source/upload an icon image themselves. Served from the
    # cryptocurrency-icons CDN (same open-source set used across the industry).
    WALLET_ICON_MAP = {
        "bitcoin":       "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/btc.png",
        "ethereum":      "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/eth.png",
        "usdt_trc20":    "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/usdt.png",
        "usdt_erc20":    "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/usdt.png",
        "bnb":           "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/bnb.png",
        "usdc":          "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/usdc.png",
        "litecoin":      "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/ltc.png",
        "ripple":        "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/xrp.png",
        "solana":        "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/sol.png",
        "dogecoin":      "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/doge.png",
        "tron":          "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/trx.png",
        "polygon":       "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/matic.png",
        "avalanche":     "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/avax.png",
        "bitcoin_cash":  "https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/bch.png",
    }

    name      = models.CharField(max_length=30, choices=WALLET_TYPE_CHOICES)
    symbol    = models.CharField(max_length=20)
    network   = models.CharField(max_length=100, blank=True, default="")
    address   = models.CharField(max_length=500)
    icon      = CloudinaryField(
        "icon", folder="wallet_icons", null=True, blank=True,
        help_text="Legacy manual override — no longer needed. The icon is now "
                   "picked automatically from the selected currency.",
    )
    qr_code   = CloudinaryField(
        "qr_code", folder="wallet_qr_codes", null=True, blank=True,
        help_text="Optional. Upload the wallet's official QR (e.g. from your exchange/wallet "
                   "app) if it needs to encode more than just the raw address — such as a "
                   "memo/destination tag some coins require. Leave blank to auto-generate a "
                   "QR from the address instead.",
    )
    is_active = models.BooleanField(default=True)
    order     = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if self.name in self.WALLET_DEFAULTS:
            default_symbol, default_network = self.WALLET_DEFAULTS[self.name]
            if not self.symbol:
                self.symbol = default_symbol
            if not self.network:
                self.network = default_network
        super().save(*args, **kwargs)

    def get_icon_url(self):
        """The icon shown for this wallet — always the brand icon for the
        chosen currency. Never a manual upload, even a legacy one already
        sitting in `icon` from before this was locked down."""
        return self.WALLET_ICON_MAP.get(self.name, "")

    def __str__(self):
        return f"{self.get_name_display()} — {self.address[:30]}…"


# ─────────────────────────────────────────────────────────────────────────────
# CryptoPrice — live prices fetched from FMP, used to calculate deposit units
# ─────────────────────────────────────────────────────────────────────────────

class CryptoPrice(models.Model):
    symbol    = models.CharField(max_length=20, unique=True)  # BTC, ETH, USDT …
    price_usd = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol}: ${self.price_usd}"


# ─────────────────────────────────────────────────────────────────────────────
# Stock data — fetched from FMP and stored locally
# ─────────────────────────────────────────────────────────────────────────────

class StockProfile(models.Model):
    """Static-ish stock metadata — refreshed daily."""
    symbol      = models.CharField(max_length=20, unique=True)
    name        = models.CharField(max_length=200, default="")
    sector      = models.CharField(max_length=100, default="")
    exchange    = models.CharField(max_length=50, default="")
    domain      = models.CharField(max_length=200, default="")
    logo_url    = models.URLField(max_length=500, blank=True, default="")
    description = models.TextField(default="")
    high_52w    = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    low_52w     = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    div_yield   = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    beta        = models.DecimalField(max_digits=8,  decimal_places=4, default=0)
    avg_vol     = models.BigIntegerField(default=0)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} — {self.name}"


class StockQuote(models.Model):
    """Live price data — refreshed every 10–15 min. Also stores index quotes."""
    symbol     = models.CharField(max_length=20, unique=True)
    price      = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    change     = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    change_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    volume     = models.BigIntegerField(default=0)
    market_cap = models.BigIntegerField(default=0)
    pe         = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    eps        = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    is_index   = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol}: ${self.price}"


class StockHistory(models.Model):
    """20-day EOD closing prices for sparkline display — refreshed daily."""
    symbol     = models.CharField(max_length=20, unique=True)
    prices     = models.JSONField(default=list)  # oldest → newest
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} history ({len(self.prices)} pts)"


# ─────────────────────────────────────────────────────────────────────────────
# News — fetched from FMP and stored locally
# ─────────────────────────────────────────────────────────────────────────────

class News(models.Model):
    CATEGORY_CHOICES = [
        ("Crypto",      "Crypto"),
        ("Stocks",      "Stocks"),
        ("Forex",       "Forex"),
        ("Commodities", "Commodities"),
        ("Tech",        "Tech"),
        ("ETF",         "ETF"),
        ("Macro",       "Macro"),
    ]

    title        = models.CharField(max_length=500)
    summary      = models.TextField(blank=True, default="")
    content      = models.TextField(blank=True, default="")
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="Macro")
    source       = models.CharField(max_length=200, blank=True, default="")
    symbol       = models.CharField(max_length=50,  blank=True, default="")
    image_url    = models.URLField(max_length=1000, blank=True, default="")
    source_url   = models.URLField(max_length=1000, blank=True, default="", unique=True)
    published_at = models.DateTimeField()
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        indexes  = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.title[:80]


# ─────────────────────────────────────────────────────────────────────────────
# SavedPaymentMethod — a user's saved withdrawal address per admin-configured
# currency (AdminWallet). Pre-fills the address field in the Withdraw modal;
# still editable per-withdrawal so it never blocks sending elsewhere.
# ─────────────────────────────────────────────────────────────────────────────

class SavedPaymentMethod(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    wallet     = models.ForeignKey(AdminWallet, on_delete=models.CASCADE, related_name="saved_addresses")
    address    = models.CharField(max_length=500)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "wallet")
        ordering = ["wallet__order", "wallet__name"]

    def __str__(self):
        return f"{self.user} — {self.wallet.symbol}: {self.address[:24]}…"


# ─────────────────────────────────────────────────────────────────────────────
# WalletConnection — a user's linked external crypto wallet.
# Only a public wallet address is ever collected/stored — never a seed
# phrase or private key. A real wallet integration verifies ownership via
# a signing protocol (e.g. WalletConnect) rather than a secret typed into
# a web form.
# ─────────────────────────────────────────────────────────────────────────────

class WalletConnection(models.Model):
    WALLET_TYPES = [
        ("aktionariat",  "Aktionariat Wallet"),
        ("binance",      "Binance Wallet"),
        ("bitcoin",      "Bitcoin Wallet"),
        ("bitkeep",      "Bitkeep Wallet"),
        ("bitpay",       "Bitpay"),
        ("blockchain",   "Blockchain"),
        ("coinbase",     "Coinbase Wallet"),
        ("coinbase-one", "Coinbase One"),
        ("crypto",       "Crypto Wallet"),
        ("exodus",       "Exodus Wallet"),
        ("gemini",       "Gemini"),
        ("imtoken",      "Imtoken"),
        ("infinito",     "Infinito Wallet"),
        ("infinity",     "Infinity Wallet"),
        ("keyringpro",   "Keyringpro Wallet"),
        ("metamask",     "Metamask"),
        ("ownbit",       "Ownbit Wallet"),
        ("phantom",      "Phantom Wallet"),
        ("pulse",        "Pulse Wallet"),
        ("rainbow",      "Rainbow"),
        ("robinhood",    "Robinhood Wallet"),
        ("safepal",      "Safepal Wallet"),
        ("sparkpoint",   "Sparkpoint Wallet"),
        ("trust",        "Trust Wallet"),
        ("uniswap",      "Uniswap"),
        ("walletio",     "Wallet io"),
    ]

    user           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet_connections")
    wallet_type    = models.CharField(max_length=50, choices=WALLET_TYPES)
    wallet_name    = models.CharField(max_length=100)
    wallet_address = models.CharField(max_length=255, help_text="Public wallet address only — never a seed phrase or private key.")
    is_active      = models.BooleanField(default=True)
    connected_at   = models.DateTimeField(auto_now_add=True)
    last_verified  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-connected_at"]
        unique_together = ("user", "wallet_type")
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["wallet_type"]),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.wallet_name}"
