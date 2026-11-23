"""
Deposit wallet resolution shared by the user-facing deposit API and the admin
"Create Deposit" page, so both always offer the same wallets, addresses and
rates.

A user's active UserAdminWallet supersedes the general AdminWallet with the
same currency (`name`). Special wallets are listed first (the deposit modal
pre-selects the first wallet) and are identified by a NEGATIVE id (-pk), so a
`wallet_id` coming from the frontend is unambiguous:
    wallet_id > 0  -> AdminWallet (general)
    wallet_id < 0  -> that user's own UserAdminWallet
"""
from decimal import Decimal

from .models import AdminWallet, CryptoPrice, UserAdminWallet


def deposit_wallets_for(user=None):
    """Active wallets this user sees, special ones first. user=None -> general only."""
    special = []
    if user is not None and getattr(user, "is_authenticated", False):
        special = list(UserAdminWallet.objects.filter(user=user, is_active=True))
    overridden = {w.name for w in special}
    general = [w for w in AdminWallet.objects.filter(is_active=True) if w.name not in overridden]
    return special + general


def wallet_api_id(wallet):
    return wallet.api_id if isinstance(wallet, UserAdminWallet) else wallet.pk


def resolve_deposit_wallet(user, wallet_id):
    """The active wallet a wallet_id refers to for this user, or None.
    Negative ids only ever resolve to the requesting user's own special wallet."""
    try:
        wallet_id = int(wallet_id)
    except (TypeError, ValueError):
        return None
    if wallet_id > 0:
        return AdminWallet.objects.filter(pk=wallet_id, is_active=True).first()
    if wallet_id < 0 and user is not None and getattr(user, "is_authenticated", False):
        return UserAdminWallet.objects.filter(pk=-wallet_id, user=user, is_active=True).first()
    return None


def deposit_rate(symbol):
    """Live USD price per unit, or None when unavailable (deposit then falls back to 1:1)."""
    cp = CryptoPrice.objects.filter(symbol=symbol).first()
    if cp and cp.price_usd and cp.price_usd > 0:
        return cp.price_usd
    return None


def deposit_units(symbol, amount_usd):
    """Crypto units for a USD amount — same rule the deposit modal has always used."""
    rate = deposit_rate(symbol)
    if rate:
        return (amount_usd / rate).quantize(Decimal("0.00000001"))
    return amount_usd
