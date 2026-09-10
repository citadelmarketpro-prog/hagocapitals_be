from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication
from .models import Notification, WalletConnection

WALLET_NAME_BY_TYPE = dict(WalletConnection.WALLET_TYPES)


class WalletListView(APIView):
    """GET /api/wallets/ -- the user's connected wallets."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        wallets = WalletConnection.objects.filter(user=request.user, is_active=True).order_by("-connected_at")
        return Response({
            "success": True,
            "wallets": [
                {
                    "id": w.id,
                    "wallet_type": w.wallet_type,
                    "wallet_name": w.wallet_name,
                    "wallet_address": w.wallet_address,
                    "connected_at": w.connected_at.isoformat(),
                    "last_verified": w.last_verified.isoformat(),
                }
                for w in wallets
            ],
        })


class WalletConnectView(APIView):
    """POST /api/wallets/connect/ -- connect a wallet by its public address."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        user           = request.user
        wallet_type    = (request.data.get("wallet_type") or "").strip()
        wallet_address = (request.data.get("wallet_address") or "").strip()
        wallet_name    = WALLET_NAME_BY_TYPE.get(wallet_type)

        if not wallet_type or not wallet_name or not wallet_address:
            return Response({
                "success": False,
                "error": "Wallet type and wallet address are required.",
            }, status=status.HTTP_400_BAD_REQUEST)

        wallet, created = WalletConnection.objects.get_or_create(
            user=user,
            wallet_type=wallet_type,
            defaults={
                "wallet_name": wallet_name,
                "wallet_address": wallet_address,
                "is_active": True,
            },
        )

        if not created:
            if wallet.is_active:
                return Response({
                    "success": False,
                    "error": "This wallet type is already connected.",
                }, status=status.HTTP_400_BAD_REQUEST)
            wallet.wallet_address = wallet_address
            wallet.is_active = True
            wallet.save(update_fields=["wallet_address", "is_active"])

        Notification.objects.create(
            user=user,
            notif_type="wallet",
            title="Wallet Connected Successfully",
            body=f"{wallet_name} has been connected to your account.",
        )

        return Response({
            "success": True,
            "message": "Wallet connected successfully",
            "wallet": {
                "id": wallet.id,
                "wallet_type": wallet.wallet_type,
                "wallet_name": wallet.wallet_name,
                "connected_at": wallet.connected_at.isoformat(),
            },
        })


class WalletDisconnectView(APIView):
    """DELETE /api/wallets/<wallet_type>/disconnect/"""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def delete(self, request, wallet_type):
        wallet = WalletConnection.objects.filter(
            user=request.user, wallet_type=wallet_type, is_active=True,
        ).first()
        if not wallet:
            return Response({
                "success": False, "error": "Wallet connection not found",
            }, status=status.HTTP_404_NOT_FOUND)

        wallet.is_active = False
        wallet.save(update_fields=["is_active"])

        Notification.objects.create(
            user=request.user,
            notif_type="wallet",
            title="Wallet Disconnected",
            body=f"{wallet.wallet_name} has been disconnected from your account.",
        )

        return Response({"success": True, "message": "Wallet disconnected successfully"})
