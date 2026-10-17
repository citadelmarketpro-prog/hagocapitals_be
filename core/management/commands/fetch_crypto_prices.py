from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand

from core import fmp_client
from core.models import CryptoPrice

# Our wallet symbol -> FMP crypto ticker
FMP_TICKER_MAP = {
    "BTC":   "BTCUSD",
    "ETH":   "ETHUSD",
    "BNB":   "BNBUSD",
    "LTC":   "LTCUSD",
    "XRP":   "XRPUSD",
    "SOL":   "SOLUSD",
    "DOGE":  "DOGEUSD",
    "TRX":   "TRXUSD",
    "MATIC": "MATICUSD",
    "AVAX":  "AVAXUSD",
    "BCH":   "BCHUSD",
}

# Stablecoins are pegged rather than pulled from FMP: avoids noisy/missing
# quotes for a price that should always read as ~$1.
STABLECOIN_SYMBOLS = ["USDT", "USDC"]


class Command(BaseCommand):
    help = "Fetch current crypto prices from FMP for deposit unit calculation."

    def handle(self, *args, **options):
        updated = skipped = 0

        for symbol in STABLECOIN_SYMBOLS:
            CryptoPrice.objects.update_or_create(
                symbol=symbol, defaults={"price_usd": Decimal("1.000000")}
            )
            updated += 1

        tickers = list(FMP_TICKER_MAP.values())
        try:
            quotes = fmp_client.get_crypto_quotes_parallel(tickers)
        except Exception as exc:
            self.stderr.write(f"FMP request failed: {exc}")
            return

        quotes_by_ticker = {q.get("symbol"): q for q in quotes if isinstance(q, dict)}

        for local_sym, ticker in FMP_TICKER_MAP.items():
            quote = quotes_by_ticker.get(ticker)
            raw_price = quote.get("price") if quote else None
            try:
                price = Decimal(str(raw_price))
            except (InvalidOperation, TypeError):
                skipped += 1
                continue

            if price <= 0:
                skipped += 1
                continue

            CryptoPrice.objects.update_or_create(
                symbol=local_sym, defaults={"price_usd": price}
            )
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Crypto prices: {updated} updated, {skipped} skipped (zero/invalid price)"
            )
        )
