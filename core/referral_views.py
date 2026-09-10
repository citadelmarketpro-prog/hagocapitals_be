import secrets
import string

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication
from .models import Transaction, User

REFERRAL_BONUS_RATE = 10  # % of a referred user's first completed deposit


def generate_unique_referral_code():
    """Generate a unique 8-character referral code (uppercase letters + digits)."""
    while True:
        code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        if not User.objects.filter(referral_code=code).exists():
            return code


class ReferralInfoView(APIView):
    """GET /api/auth/referral/info/ -- current user's referral code, link and stats."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.referral_code:
            user.referral_code = generate_unique_referral_code()
            user.save(update_fields=["referral_code"])

        frontend_url = request.headers.get("X-Frontend-URL", settings.FRONTEND_URL)
        referral_link = f"{frontend_url}/sign-up?ref={user.referral_code}"

        total_referrals = User.objects.filter(referred_by=user).count()

        return Response({
            "success": True,
            "referral_data": {
                "referral_code": user.referral_code,
                "referral_link": referral_link,
                "total_referrals": total_referrals,
                "total_earnings": str(user.referral_bonus_earned or 0),
                "referral_bonus_rate": REFERRAL_BONUS_RATE,
            },
        })


class ReferralListView(APIView):
    """GET /api/auth/referral/list/ -- users referred by the current user."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        referrals = User.objects.filter(referred_by=request.user).order_by("-date_joined")

        referrals_list = []
        for referred_user in referrals:
            first_deposit = Transaction.objects.filter(
                user=referred_user, tx_type="deposit", status="completed",
            ).order_by("created_at").first()

            bonus_earned = float(first_deposit.amount_usd) * (REFERRAL_BONUS_RATE / 100) if first_deposit else 0

            referrals_list.append({
                "id": referred_user.id,
                "email": referred_user.email,
                "first_name": referred_user.first_name or "",
                "last_name": referred_user.last_name or "",
                "date_joined": referred_user.date_joined.isoformat() if referred_user.date_joined else None,
                "has_deposited": first_deposit is not None,
                "bonus_earned": str(bonus_earned),
            })

        return Response({"success": True, "referrals": referrals_list})


class ReferralGenerateView(APIView):
    """POST /api/auth/referral/generate/ -- generate or regenerate the referral code."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        user  = request.user
        force = request.data.get("force", False)

        if user.referral_code and not force:
            return Response({
                "success": False,
                "error": "You already have a referral code. Set 'force' to true to regenerate.",
            }, status=status.HTTP_400_BAD_REQUEST)

        had_code = bool(user.referral_code)
        user.referral_code = generate_unique_referral_code()
        user.save(update_fields=["referral_code"])

        frontend_url  = request.headers.get("X-Frontend-URL", settings.FRONTEND_URL)
        referral_link = f"{frontend_url}/sign-up?ref={user.referral_code}"
        message = "Referral code regenerated successfully!" if had_code else "Referral code generated successfully!"

        return Response({
            "success": True,
            "message": message,
            "referral_code": user.referral_code,
            "referral_link": referral_link,
        })


class ReferralValidateView(APIView):
    """GET /api/auth/referral/validate/?code=XXXX -- validate a referral code (public)."""
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code", "").strip().upper()
        if not code:
            return Response({
                "success": False, "valid": False, "error": "No referral code provided",
            }, status=status.HTTP_400_BAD_REQUEST)

        referrer = User.objects.filter(referral_code=code).first()
        if not referrer:
            return Response({"success": True, "valid": False, "error": "Invalid referral code"})

        name = f"{referrer.first_name} {referrer.last_name}".strip() or referrer.username
        return Response({
            "success": True,
            "valid": True,
            "referrer": {"name": name, "email": referrer.email},
        })
