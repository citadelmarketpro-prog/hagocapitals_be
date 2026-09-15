"""
Trading Signals — user-facing API.

Logic ported from orchard_capitals' app/signal_views.py: list active signals
with a per-user "already purchased" flag, purchase a signal (deduct balance,
record a JSON snapshot so terms don't drift if the signal is edited later),
and list what the user has purchased.
"""

from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication
from .models import Notification, Signal, UserSignalPurchase


def _signal_dict(signal: Signal) -> dict:
    return {
        "id": signal.id,
        "name": signal.name,
        "signal_type": signal.signal_type,
        "price": str(signal.price),
        "signal_strength": str(signal.signal_strength),
        "market_analysis": signal.market_analysis,
        "entry_point": signal.entry_point,
        "target_price": signal.target_price,
        "stop_loss": signal.stop_loss,
        "action": signal.action,
        "timeframe": signal.timeframe,
        "risk_level": signal.risk_level,
        "technical_indicators": signal.technical_indicators,
        "fundamental_analysis": signal.fundamental_analysis,
        "status": signal.status,
        "is_featured": signal.is_featured,
        "created_at": signal.created_at.isoformat(),
        "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,
    }


class SignalListView(APIView):
    """GET /api/auth/signals/ — active signals + this user's purchase status."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        user = request.user
        signals = Signal.objects.filter(is_active=True).order_by("-is_featured", "-created_at")
        purchased_ids = set(
            UserSignalPurchase.objects.filter(user=user).values_list("signal_id", flat=True)
        )

        signals_list = []
        for signal in signals:
            row = _signal_dict(signal)
            row["is_purchased"] = signal.id in purchased_ids
            signals_list.append(row)

        return Response({
            "success": True,
            "signals": signals_list,
            "user_balance": str(user.balance),
        })


class SignalPurchaseView(APIView):
    """POST /api/auth/signals/<pk>/purchase/ — buy a signal, deduct balance."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user

        try:
            signal = Signal.objects.get(pk=pk, is_active=True)
        except Signal.DoesNotExist:
            return Response(
                {"success": False, "error": "Signal not found or no longer available"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if UserSignalPurchase.objects.filter(user=user, signal=signal).exists():
            return Response(
                {"success": False, "error": "You have already purchased this signal"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.balance < signal.price:
            return Response({
                "success": False,
                "error": f"Insufficient balance. You need ${signal.price} but only have ${user.balance}",
                "required": str(signal.price),
                "current_balance": str(user.balance),
            }, status=status.HTTP_400_BAD_REQUEST)

        user.balance -= signal.price
        user.save(update_fields=["balance"])

        purchase_reference = f"SIG-{get_random_string(12).upper()}"
        signal_snapshot = _signal_dict(signal)

        UserSignalPurchase.objects.create(
            user=user,
            signal=signal,
            amount_paid=signal.price,
            purchase_reference=purchase_reference,
            signal_data=signal_snapshot,
        )

        Notification.objects.create(
            user=user,
            notif_type="trade",
            title="Signal Purchased Successfully",
            body=(
                f"You have successfully purchased {signal.name} signal for ${signal.price}. "
                f"Reference: {purchase_reference}."
            ),
        )

        return Response({
            "success": True,
            "message": "Signal purchased successfully",
            "purchase_reference": purchase_reference,
            "new_balance": str(user.balance),
        })


class PurchasedSignalListView(APIView):
    """GET /api/auth/signals/purchased/ — this user's purchased signals."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        purchases = (
            UserSignalPurchase.objects.filter(user=request.user)
            .select_related("signal")
            .order_by("-purchased_at")
        )

        purchases_list = []
        for purchase in purchases:
            signal = purchase.signal
            purchases_list.append({
                "id": purchase.id,
                "signal_id": signal.id,
                "signal_name": signal.name,
                "signal_type": signal.signal_type,
                "amount_paid": str(purchase.amount_paid),
                "purchase_reference": purchase.purchase_reference,
                "purchased_at": purchase.purchased_at.isoformat(),
                "signal_data": purchase.signal_data,
                # Current live signal data, if the admin hasn't deactivated it —
                # otherwise the frontend falls back to signal_data (the snapshot).
                "current_signal": _signal_dict(signal) if signal.is_active else None,
            })

        return Response({"success": True, "purchases": purchases_list})
