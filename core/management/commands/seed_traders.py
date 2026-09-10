"""
python manage.py seed_traders
python manage.py seed_traders --clear

Seeds Trader records with realistic demo data. Traders are standalone
profiles — no User account is needed or created. Field set matches
orchard_capitals' Trader model (portfolio_breakdown/top_traded/tags are
plain JSON fields on Trader, not separate relational tables).

Run in development only.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Trader

# ─────────────────────────────────────────────────────────────────────────────
# Trader seed data
# Each tuple:
#   (name, bio, category, risk, gain, copiers, followers, min_capital,
#    trading_days, max_drawdown, cum_earnings, cum_copiers, win_rate_pct, tags)
# ─────────────────────────────────────────────────────────────────────────────

TRADERS = [
    # ── Trending Investors ──────────────────────────────────────────────────
    ("Jordan Blake", "Since 2020, my portfolio has seen a growth of 32%. Join me to replicate my success on these markets.",
     "stocks", 4, 32.50, 740, 320, 50000, 1095, 9.87, 312480.25, 11235, 95.20, ["Equities", "Stocks"]),
    ("Linda Johnson", "My trading strategies have yielded a 21% increase since 2016. Let's trade together and grow.",
     "stocks", 2, 28.75, 490, 210, 30000, 2555, 7.50, 245000.00, 8900, 91.50, ["Market Analyst", "Blue Chips"]),
    ("Carlos Mendoza", "With a 30% portfolio growth since 2019, I'm ready to share my insights with you.",
     "stocks", 5, 29.05, 612, 280, 40000, 1460, 11.20, 278000.00, 9500, 88.70, ["Investment Analyst", "Growth Stocks"]),
    ("Emma Lee", "My portfolio has yielded by 28%. Copy my trades and let's grow together.",
     "stocks", 4, 30.15, 504, 230, 35000, 1825, 8.90, 260000.00, 9100, 92.30, ["Stocks", "Equities"]),
    ("Marcus Vael", "Leverage my 9.8% average monthly return with data-driven strategies built over 5+ years.",
     "stocks", 5, 27.90, 381, 185, 25000, 1825, 12.50, 198000.00, 7200, 86.40, ["Quant", "Tech Stocks"]),

    # ── Rising Stars ─────────────────────────────────────────────────────────
    ("Liam O'Connor", "Specialising in order flow analysis to capture short-term momentum. Steady and growing.",
     "stocks", 5, 18.75, 320, 145, 15000, 365, 14.30, 120000.00, 4500, 82.10, []),
    ("Sofia Martinez", "High-conviction stock plays with defined risk. Consistent alpha since I started.",
     "stocks", 7, 22.10, 412, 190, 20000, 548, 18.40, 158000.00, 5800, 79.60, []),
    ("Ethan Zhang", "Focused on high-growth equities and macro trends. Low risk, steady compounding.",
     "stocks", 2, 15.50, 210, 98, 10000, 730, 6.10, 85000.00, 3200, 89.30, []),
    ("Nia Thompson", "Using blue-chip and dividend stocks for consistent, safe returns. Capital preservation first.",
     "stocks", 1, 20.85, 310, 140, 18000, 456, 5.80, 135000.00, 5000, 93.70, []),
    ("Aiden Park", "Riding breakouts and momentum plays across tech and growth equities.",
     "stocks", 5, 19.40, 278, 128, 12000, 420, 13.20, 105000.00, 3900, 84.50, []),

    # ── Most Copied by Categories ────────────────────────────────────────────
    ("Evelyn Dubois", "Top-ranked equities trader with consistent alpha generation through disciplined setups.",
     "stocks", 7, 32.53, 789, 360, 55000, 1642, 10.20, 342000.00, 12500, 94.10, []),
    ("Mateo Vargas", "Full-time day trader specialising in high-probability stock setups. Consistency is my edge.",
     "stocks", 5, 28.79, 634, 298, 45000, 1460, 9.50, 285000.00, 10400, 90.80, []),
    ("Aaliyah Ramirez", "Patient value investor. I find mispriced stocks and let compounding do the rest.",
     "stocks", 2, 26.19, 592, 275, 40000, 2190, 7.30, 255000.00, 9300, 91.20, []),
    ("Jamieson Patel", "Swing trading major indices and blue-chip stocks. Risk management is paramount.",
     "stocks", 2, 25.64, 578, 268, 38000, 1825, 8.10, 248000.00, 9000, 90.10, []),
    ("Scarlett Nguyen", "Systematic algo strategies on equities running 24/7. Data-driven, emotion-free.",
     "stocks", 5, 25.22, 562, 260, 36000, 1460, 9.80, 238000.00, 8700, 89.60, []),
    ("Kellan O'Connell", "Rotating capital across leading equity sectors. Technically driven with strict risk rules.",
     "stocks", 2, 24.91, 555, 255, 34000, 1825, 7.60, 230000.00, 8500, 88.90, []),
    ("Zoya Rhodes", "High-yield dividend stocks and income equities. Hedging market risks with precision.",
     "stocks", 4, 24.67, 548, 252, 32000, 1642, 10.40, 225000.00, 8200, 87.30, []),
    ("Kael Kline", "Combining crowd intelligence with technical analysis on equities for superior returns.",
     "stocks", 4, 24.35, 539, 248, 30000, 1095, 11.20, 218000.00, 8000, 86.80, []),
    ("Jaslyn Kaiser", "Capturing alpha through earnings, M&A, and macro events in equities. Disciplined sizing.",
     "stocks", 2, 24.02, 530, 244, 28000, 1825, 8.90, 210000.00, 7700, 88.10, []),
    ("Braden Acosta", "Pure quant on equities. Every trade is backed by statistical models and rigorous back-testing.",
     "stocks", 4, 23.88, 526, 240, 26000, 1460, 12.10, 205000.00, 7500, 85.70, []),

    # ── Reliable Traders ─────────────────────────────────────────────────────
    ("Elias Rossi", "My priority is capital preservation. Steady stock returns with minimal drawdowns.",
     "stocks", 4, 15.23, 342, 158, 20000, 1460, 6.40, 112000.00, 4100, 90.50, []),
    ("Naomi Walker", "Diversified, well-researched equity portfolio management. Low risk, consistent growth.",
     "stocks", 2, 18.92, 412, 190, 25000, 1825, 5.20, 148000.00, 5400, 92.80, []),
    ("Damian Green", "Long-only, quality growth stocks. Patient approach delivering real returns.",
     "stocks", 2, 12.55, 289, 132, 15000, 2190, 4.80, 88000.00, 3200, 91.30, []),
    ("Isabelle Flores", "Top-down macro approach across global equities and indices. Balanced risk profile.",
     "stocks", 4, 16.47, 380, 175, 22000, 1642, 7.90, 125000.00, 4600, 89.70, []),
    ("Omar Fayed", "Focused on blue-chip and dividend stocks. Safety first, with a focus on real yield.",
     "stocks", 2, 14.10, 265, 120, 18000, 1825, 4.10, 98000.00, 3600, 93.10, []),

    # ── Proven Stability ─────────────────────────────────────────────────────
    ("Julian Hayes", "Quant strategies on equities with a focus on long-term risk-adjusted returns.",
     "stocks", 2, 22.51, 497, 228, 30000, 2190, 6.70, 195000.00, 7100, 90.20, ["Quant Trader", "Tech Stocks"]),
    ("Aurora Chen", "Growth and momentum equities with a track record of consistent alpha and controlled risk.",
     "stocks", 4, 25.84, 584, 268, 38000, 1825, 8.30, 228000.00, 8300, 91.60, ["Growth Stocks", "Equities"]),
    ("Declan Ward", "Algo and AI-driven equity strategies. Fully systematic, fully transparent.",
     "stocks", 4, 21.39, 465, 214, 28000, 1642, 9.40, 178000.00, 6500, 88.30, ["Algo Trading", "AI Trading"]),
    ("Anya Petrova", "Deep value, long-term stock investor. I buy great businesses at fair prices.",
     "stocks", 2, 19.76, 420, 192, 25000, 2555, 5.60, 158000.00, 5800, 92.50, ["Value Investing", "Long-Term Value"]),
    ("Felix Andrade", "Cross-sector equity portfolio spanning large caps, mid caps, and growth plays.",
     "stocks", 4, 23.05, 511, 234, 32000, 1825, 10.80, 198000.00, 7200, 87.90, ["Macro", "Equities"]),

    # ── Detail page hero trader ──────────────────────────────────────────────
    ("Elias Nunez", "Hi, I'm Elias! My stock portfolio has grown by 35% this year. Start copying my trades today!",
     "stocks", 2, 35.12, 789, 342, 138696, 612, 9.87, 312480.25, 11235, 95.20,
     ["Risk guru", "Large Cap", "Growth Stocks", "Leverage Expert", "Volatility Guru"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# Detail data templates — scaled per trader by their gain
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATE_TOP_TRADED = [
    # (name, ticker, avg_profit, avg_loss, profitable_pct)
    ("Gold",     "XAU",  21.45, -5.22, 88.50),
    ("S&P 500",  "SPX",  19.78, -4.89, 92.70),
    ("EUR/USD",  "EUR",  17.34, -6.15, 89.10),
    ("Apple",    "AAPL", 20.55, -3.92, 94.30),
    ("Ethereum", "ETH",  16.81, -7.29, 81.70),
]

TEMPLATE_PORTFOLIO_BREAKDOWN = [
    # (name, percentage)
    ("Forex",   30),
    ("Stocks",  35),
    ("Indices", 35),
]


def _win_loss_from_rate(win_rate_pct: float, total_trades: int = 1000) -> tuple[int, int]:
    """orchard_capitals stores win_rate as a derived @property (total_wins /
    (total_wins+total_losses)) rather than a raw column — back-solve a
    plausible (wins, losses) pair that reproduces the seed data's intended
    win rate exactly."""
    wins = round(total_trades * win_rate_pct / 100)
    return wins, total_trades - wins


class Command(BaseCommand):
    help = "Seed Trader records with full detail data. Traders are standalone — no User accounts created."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing Trader records before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Trader.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} trader record(s)."))

        created_count = 0
        skipped_count = 0

        for (
            name, bio, category, risk, gain, copiers, followers, min_capital,
            trading_days, max_drawdown, cum_earnings, cum_copiers, win_rate_pct,
            tags,
        ) in TRADERS:

            scale = Decimal(str(gain)) / Decimal("25")
            total_wins, total_losses = _win_loss_from_rate(win_rate_pct)

            top_traded = [
                {
                    "name": aname, "ticker": ticker,
                    "avg_profit": round(avg_p * float(scale), 2),
                    "avg_loss":   round(avg_l * float(scale), 2),
                    "profitable_pct": min(99.99, round(success * float(scale), 2)),
                }
                for aname, ticker, avg_p, avg_l, success in TEMPLATE_TOP_TRADED
            ]
            portfolio_breakdown = [
                {"name": label, "percentage": pct} for label, pct in TEMPLATE_PORTFOLIO_BREAKDOWN
            ]
            frequently_traded = [ticker for _n, ticker, *_ in TEMPLATE_TOP_TRADED]

            trader, created = Trader.objects.get_or_create(
                name=name,
                defaults={
                    "bio":            bio,
                    "category":       category,
                    "risk":           risk,
                    "gain":           Decimal(str(gain)),
                    "copiers":        copiers,
                    "followers":      followers,
                    "min_account_threshold": Decimal(str(min_capital)),
                    "trading_days":   trading_days,
                    "max_drawdown":   Decimal(str(max_drawdown)),
                    "cumulative_earnings_copiers": Decimal(str(cum_earnings)),
                    "cumulative_copiers": cum_copiers,
                    "total_wins":     total_wins,
                    "total_losses":   total_losses,
                    "tags":           tags,
                    "top_traded":     top_traded,
                    "portfolio_breakdown": portfolio_breakdown,
                    "frequently_traded":   frequently_traded,
                },
            )

            if not created:
                self.stdout.write(f"  skip   {name} (already exists)")
                skipped_count += 1
                continue

            self.stdout.write(self.style.SUCCESS(f"  created {name}"))
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {created_count} trader(s) created, {skipped_count} skipped."
        ))
