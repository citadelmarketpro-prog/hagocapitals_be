"""
Email service for HagoCapitals
HTML email templates styled to match the HagoCapitals brand.
"""

import random
import time
import resend
from django.conf import settings
from django.utils import timezone
from django.utils.html import escape, linebreaks
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Core send utility
# ─────────────────────────────────────────────────────────────────────────────

def generate_verification_code():
    """Generate a random 4-digit verification code."""
    return str(random.randint(1000, 9999))


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an HTML email via Resend API."""
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        })
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def is_code_valid(user) -> bool:
    """Return True if the user's verification code is still within 10 minutes."""
    if not getattr(user, "code_created_at", None) or not getattr(user, "verification_code", None):
        return False
    return timezone.now() < user.code_created_at + timedelta(minutes=10)


# ─────────────────────────────────────────────────────────────────────────────
# Shared template helpers
# ─────────────────────────────────────────────────────────────────────────────
#
# Brand palette (mirrors frontend CSS tokens):
#   --background      : #0b1c11   (dark green page bg)
#   --card            : #132b1a   (card bg)
#   --card-border     : #1e3827
#   --primary         : #B0D45A   (lime green)
#   --foreground      : #f0f0f0
#   --muted-foreground: #8fa896
#   --profit          : #22c55e
#   --loss            : #f87171
#
# Emails are rendered on white backgrounds for universal client compat,
# but use the brand header + lime green accent throughout.
# ─────────────────────────────────────────────────────────────────────────────

def _base_styles() -> str:
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                         'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            background-color: #f0f2f0;
            -webkit-font-smoothing: antialiased;
        }
        .wrapper {
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        }

        /* ── Header ── */
        .header {
            background-color: #0b1c11;
            padding: 32px 40px 28px;
        }
        .header-logo {
            font-size: 21px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.3px;
        }
        .header-logo span {
            color: #B0D45A;
        }
        .header-tagline {
            font-size: 11px;
            color: #8fa896;
            margin-top: 4px;
            letter-spacing: 0.6px;
            text-transform: uppercase;
        }
        .header-divider {
            width: 36px;
            height: 2px;
            background-color: #B0D45A;
            margin-top: 18px;
        }
        .header-logo-chip {
            display: inline-block;
            background-color: #ffffff;
            border-radius: 8px;
            padding: 10px 16px;
            line-height: 0;
        }

        /* ── Body ── */
        .body-content {
            padding: 40px;
        }
        .greeting {
            font-size: 14px;
            color: #6b7c6b;
            margin-bottom: 20px;
        }
        .heading {
            font-size: 22px;
            font-weight: 700;
            color: #0b1c11;
            margin-bottom: 14px;
            line-height: 1.3;
        }
        .text {
            font-size: 14px;
            color: #4b5c4b;
            margin-bottom: 22px;
            line-height: 1.75;
        }
        .divider {
            height: 1px;
            background-color: #e4ede4;
            margin: 30px 0;
        }

        /* ── CTA button ── */
        .btn {
            display: inline-block;
            padding: 13px 36px;
            background-color: #B0D45A;
            color: #0b1c11;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.2px;
        }

        /* ── Info box (lime accent) ── */
        .info-box {
            background-color: #f3f9e6;
            border-left: 3px solid #B0D45A;
            padding: 16px 20px;
            margin: 22px 0;
            border-radius: 0 4px 4px 0;
        }
        .info-box p {
            font-size: 13px;
            color: #3a4a2a;
            margin: 4px 0;
        }

        /* ── OTP / code block ── */
        .code-container {
            background-color: #0b1c11;
            border-radius: 8px;
            padding: 30px;
            margin: 28px 0;
            text-align: center;
        }
        .code-value {
            font-size: 44px;
            font-weight: 800;
            color: #B0D45A;
            letter-spacing: 14px;
            font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
        }
        .code-label {
            font-size: 11px;
            color: #8fa896;
            margin-top: 10px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
        }

        /* ── Warning notice (amber) ── */
        .notice {
            background-color: #fffbeb;
            border-left: 3px solid #f59e0b;
            padding: 14px 18px;
            margin: 22px 0;
            border-radius: 0 4px 4px 0;
        }
        .notice p {
            font-size: 13px;
            color: #78400a;
            margin: 0;
        }

        /* ── Detail table ── */
        .section-title {
            font-size: 11px;
            font-weight: 700;
            color: #8fa896;
            text-transform: uppercase;
            letter-spacing: 1.1px;
            margin-bottom: 10px;
            margin-top: 26px;
        }
        .detail-table {
            width: 100%;
            border-collapse: collapse;
            margin: 8px 0;
        }
        .detail-table td {
            padding: 10px 0;
            font-size: 13px;
            border-bottom: 1px solid #edf3ed;
        }
        .detail-table .label {
            color: #8fa896;
            width: 40%;
            font-weight: 500;
        }
        .detail-table .value {
            color: #1a2a1a;
            font-weight: 600;
            text-align: right;
        }

        /* ── Status badges ── */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-pending  { background-color: #fef3c7; color: #92400e; }
        .badge-approved { background-color: #dcfce7; color: #14532d; }
        .badge-urgent   { background-color: #fee2e2; color: #991b1b; }
        .badge-info     { background-color: #e8f5d0; color: #3a6010; }

        /* ── Amount display ── */
        .amount-box {
            border-radius: 8px;
            padding: 26px;
            text-align: center;
            margin: 24px 0;
        }
        .amount-box .amount {
            font-size: 34px;
            font-weight: 800;
        }
        .amount-box .amount-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 6px;
        }
        .amount-box.deposit  { background-color: #f0fdf4; border: 1px solid #bbf7d0; }
        .amount-box.deposit  .amount { color: #16a34a; }
        .amount-box.deposit  .amount-label { color: #4b7a4b; }
        .amount-box.withdraw { background-color: #fef2f2; border: 1px solid #fecaca; }
        .amount-box.withdraw .amount { color: #dc2626; }
        .amount-box.withdraw .amount-label { color: #7a3a3a; }
        .amount-box.neutral  { background-color: #f3f9e6; border: 1px solid #c8e886; }
        .amount-box.neutral  .amount { color: #4a7a10; }
        .amount-box.neutral  .amount-label { color: #4a6a10; }

        /* ── Link fallback ── */
        .link-fallback {
            background-color: #f4f9f4;
            border: 1px solid #d4e8d4;
            border-radius: 4px;
            padding: 12px 16px;
            margin: 18px 0;
            word-break: break-all;
            font-size: 12px;
            color: #4b6b4b;
            font-family: monospace;
        }

        /* ── Footer ── */
        .footer {
            background-color: #0d2016;
            padding: 26px 40px;
        }
        .footer-text {
            font-size: 12px;
            color: #5a7a5a;
            line-height: 1.65;
        }
        .footer-links {
            margin-top: 10px;
        }
        .footer-links a {
            color: #8fa896;
            text-decoration: none;
            font-size: 12px;
            margin-right: 16px;
        }
        .footer-brand {
            font-size: 13px;
            font-weight: 700;
            color: #B0D45A;
            margin-bottom: 6px;
        }

        /* ── Sign-off ── */
        .signature {
            margin-top: 30px;
            font-size: 14px;
            color: #4b5c4b;
        }
        .signature p {
            margin: 2px 0;
        }
        .signature-name {
            font-weight: 700;
            color: #0b1c11;
        }
    """


def _header_html() -> str:
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    # logo_one.png is drawn for a light background (it has black wordmark
    # text) — the header itself stays dark to match the rest of the brand
    # accent, so the logo sits on its own small white chip for legibility.
    logo_url = f"{frontend}/logos/logo_one.png"
    return f"""
    <div class="header">
        <div class="header-logo-chip">
            <img src="{logo_url}" alt="HagoCapitals" width="140" style="display:block; width:140px; height:auto; max-width:140px; border:0;" />
        </div>
        <div class="header-tagline">Copy Trading Platform</div>
        <div class="header-divider"></div>
    </div>
    """


# Platform key -> (glyph shown in the badge, brand color). Order controls display order.
_SOCIAL_META = {
    "facebook":  ("f",  "#1877F2"),
    "twitter":   ("X",  "#000000"),
    "instagram": ("IG", "#E1306C"),
    "linkedin":  ("in", "#0A66C2"),
    "telegram":  ("TG", "#26A5E4"),
    "youtube":   ("YT", "#FF0000"),
}
_SOCIAL_LABELS = {
    "facebook": "Facebook", "twitter": "Twitter / X", "instagram": "Instagram",
    "linkedin": "LinkedIn", "telegram": "Telegram", "youtube": "YouTube",
}


def _social_icons_html(social_links: dict | None) -> str:
    """
    Row of circular social icon badges for the footer. A platform is only
    rendered if `social_links` has a non-empty URL for it — e.g. passing
    {"facebook": "https://facebook.com/x"} renders just the Facebook icon.
    Returns "" (no row at all) when no links are provided.
    """
    if not social_links:
        return ""

    cells = []
    for key, (glyph, color) in _SOCIAL_META.items():
        url = (social_links.get(key) or "").strip()
        if not url:
            continue
        label = _SOCIAL_LABELS[key]
        cells.append(f"""
            <td style="padding:0 5px;">
                <a href="{escape(url)}" title="{label}" style="display:inline-block; width:32px; height:32px;
                   line-height:32px; background-color:{color}; border-radius:50%; text-align:center;
                   text-decoration:none; color:#ffffff; font-size:12px; font-weight:700;
                   font-family:Arial,Helvetica,sans-serif;">{glyph}</a>
            </td>""")

    if not cells:
        return ""

    return f"""
    <table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="margin:18px auto 4px;">
        <tr>{''.join(cells)}</tr>
    </table>
    """


def _footer_html(user_email: str, social_links: dict | None = None) -> str:
    frontend    = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    year        = timezone.now().year
    social_html = _social_icons_html(social_links)
    return f"""
    <div class="footer">
        <div class="footer-brand">HagoCapitals</div>
        <div class="footer-text">
            This is an automated message. Please do not reply directly to this email.
        </div>
        {social_html}
        <div class="footer-links">
            <a href="{frontend}/privacy-policy">Privacy Policy</a>
            <a href="{frontend}/terms">Terms of Service</a>
        </div>
        <div class="footer-text" style="margin-top:14px;">
            Sent to {user_email} &middot; &copy; {year} HagoCapitals. All rights reserved.
        </div>
    </div>
    """


def _signature_html() -> str:
    """Shared sign-off block used at the end of every user-facing email body,
    right before the footer."""
    return """
    <div class="signature">
        <p>Warm regards,</p>
        <p class="signature-name">The HagoCapitals Team</p>
    </div>
    """


def _admin_footer_html(note: str) -> str:
    """Branded footer for internal admin-notification emails — same visual
    identity as the user-facing footer, minus the customer-facing links."""
    year = timezone.now().year
    return f"""
    <div class="footer">
        <div class="footer-brand">HagoCapitals</div>
        <div class="footer-text">{note}</div>
        <div class="footer-text" style="margin-top:10px;">
            &copy; {year} HagoCapitals. Internal notification — not sent to the customer.
        </div>
    </div>
    """


def _wrap(body: str) -> str:
    """Wrap body HTML in a full document with shared styles."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{_base_styles()}</style>
</head>
<body>
    <div class="wrapper">
        {body}
    </div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Welcome email
# ─────────────────────────────────────────────────────────────────────────────

def send_welcome_email(user) -> bool:
    # Styled with the same shared "Citadels Market" layout as the admin
    # notification emails below (_admin_header/_admin_card/etc. — the name
    # predates this reuse, but the look is identical apart from brand/logo).
    subject = "Your HagoCapitals Account Is Ready"
    name = user.first_name or "Trader"
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    steps = [
        ("01", "Complete KYC Verification", "Submit your identification documents to unlock full trading capabilities and higher deposit limits."),
        ("02", "Fund Your Account",          "Make your first deposit and start building your portfolio with access to global markets."),
        ("03", "Copy a Pro Trader",           "Select from our curated roster of verified traders and mirror their positions automatically."),
        ("04", "Monitor &amp; Grow",          "Track your performance in real time, manage risk, and scale your investments with confidence."),
    ]
    steps_html = ""
    for num, title, desc in steps:
        steps_html += f"""
        <tr>
          <td style="padding:16px 0; border-bottom:1px solid {_ADMIN_BORDER}; vertical-align:top;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td style="width:36px; vertical-align:top; padding-top:2px;">
                  <span style="display:inline-block; width:28px; height:28px; background-color:{_ADMIN_BRAND}; border-radius:50%; text-align:center; line-height:28px; font-size:11px; font-weight:700; color:#fff;">{num}</span>
                </td>
                <td style="padding-left:14px; vertical-align:top;">
                  <p style="margin:0 0 4px; font-size:14px; font-weight:600; color:{_ADMIN_TEXT_PRIMARY};">{title}</p>
                  <p style="margin:0; font-size:13px; color:{_ADMIN_TEXT_MUTED}; line-height:1.6;">{desc}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{subject}</title>
      {_admin_base_styles()}
    </head>
    <body>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG}; padding:32px 0;">
      <tr><td align="center">
        <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG};">

          {_admin_header("Welcome to HagoCapitals", "Your account has been successfully created.", "Welcome! Your trading journey starts here.")}

          <tr>
            <td align="center" style="background-color:{_ADMIN_BODY_BG}; padding:0;">
              <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="content-padding" style="padding:32px 40px;">

                    {_admin_card(f'''
                    <p style="margin:0 0 10px; font-size:22px; font-weight:700; color:{_ADMIN_TEXT_PRIMARY};">Hello, {name}.</p>
                    <p style="margin:0; font-size:15px; color:{_ADMIN_TEXT_MUTED}; line-height:1.7;">
                      Welcome to <strong style="color:{_ADMIN_TEXT_PRIMARY};">HagoCapitals</strong> &mdash; a professional-grade copy trading platform giving you access to global markets, expert traders, and real-time market intelligence. We're glad to have you on board.
                    </p>
                    ''', padding="28px 32px")}

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:{_ADMIN_ACCENT_LIGHT}; border:1px solid #a7e8c0; border-radius:8px; margin-bottom:16px;">
                      <tr>
                        <td style="padding:18px 24px;">
                          <table cellpadding="0" cellspacing="0" border="0" width="100%">
                            <tr>
                              <td>
                                <p style="margin:0 0 2px; font-size:11px; font-weight:600; color:{_ADMIN_BRAND}; letter-spacing:1px; text-transform:uppercase;">Registered Email</p>
                                <p style="margin:0; font-size:14px; font-weight:600; color:{_ADMIN_TEXT_PRIMARY};">{user.email}</p>
                              </td>
                              <td align="right">
                                <span style="background-color:{_ADMIN_BRAND}; color:#fff; font-size:11px; font-weight:700; padding:4px 12px; border-radius:20px; letter-spacing:0.5px;">ACTIVE</span>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>

                    {_admin_card(f'''
                    {_admin_section_heading("Getting Started &mdash; 4 Simple Steps")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {steps_html}
                    </table>
                    ''', padding="28px 32px")}

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:8px;">
                      <tr>
                        <td align="center" style="padding:8px 0 24px;">
                          <a href="{frontend}/dashboard" style="display:inline-block; background-color:{_ADMIN_BRAND}; color:#ffffff; font-size:15px; font-weight:600; text-decoration:none; padding:14px 40px; border-radius:6px; letter-spacing:0.3px;">
                            Go to Dashboard &rarr;
                          </a>
                        </td>
                      </tr>
                    </table>

                    <p style="margin:0; font-size:13px; color:{_ADMIN_TEXT_MUTED}; text-align:center; line-height:1.7;">
                      Questions? Our support team is available 24/7.<br>
                      <a href="mailto:{getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'support@hagoscapitals.com')}" style="color:{_ADMIN_BRAND}; font-weight:600;">Contact Support</a>
                    </p>

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {_admin_notif_footer()}

        </table>
      </td></tr>
    </table>
    </body>
    </html>
    """
    return send_email(user.email, subject, html_content)


# ─────────────────────────────────────────────────────────────────────────────
# KYC / identity verification approved
# ─────────────────────────────────────────────────────────────────────────────

def send_kyc_approved_email(user) -> bool:
    name     = user.first_name or "Trader"
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Verification Successfully Completed</div>
        <div class="text">
            Your identity verification has been approved.
        </div>
        <div style="margin:22px 0 26px;">
            <span style="font-size:13px; color:#4b5c4b; font-weight:600;">Account Verification:</span>
            <span class="badge badge-approved" style="margin-left:8px;">&#10003; Verified</span>
        </div>
        <div class="text">
            You can now fund your account and access the available traders and
            mirror-trading strategies from your client dashboard.
        </div>
        <div style="text-align:center; margin:32px 0;">
            <a href="{frontend}/dashboard" class="btn">
                Go to Client Dashboard
            </a>
        </div>
        <div class="divider"></div>
        <div class="signature">
            <p>Thank you,</p>
            <p class="signature-name">Hago Capitals</p>
            <p>Account Verification Department</p>
        </div>
    </div>
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Verification Successfully Completed", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# Email verification (OTP code)
# ─────────────────────────────────────────────────────────────────────────────

def send_verification_code_email(user, code: str) -> bool:
    name = user.first_name or "Trader"
    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Verify your email address</div>
        <div class="text">
            To complete your HagoCapitals registration, enter the code below.
            It expires in <strong>10 minutes</strong>.
        </div>
        <div class="code-container">
            <div class="code-value">{code}</div>
            <div class="code-label">Email Verification Code</div>
        </div>
        <div class="notice">
            <p><strong>Security reminder:</strong> Never share this code with anyone.
            HagoCapitals will never ask for your code via phone or live chat.</p>
        </div>
        <div class="divider"></div>
        <div class="text" style="font-size:13px; color:#8fa896;">
            If you did not create a HagoCapitals account, you can safely ignore this email.
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Verify your email — HagoCapitals", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# Two-factor authentication code
# ─────────────────────────────────────────────────────────────────────────────

def send_2fa_code_email(user, code: str) -> bool:
    name = user.first_name or "Trader"
    now  = timezone.now().strftime("%b %d, %Y at %I:%M %p UTC")
    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Two-factor authentication</div>
        <div class="text">
            A sign-in attempt was detected on your account. Enter the code below to
            complete authentication. This code expires in <strong>10 minutes</strong>.
        </div>
        <div class="code-container">
            <div class="code-value">{code}</div>
            <div class="code-label">Authentication Code</div>
        </div>
        <table class="detail-table" style="margin-top:0;">
            <tr>
                <td class="label">Account</td>
                <td class="value">{user.email}</td>
            </tr>
            <tr>
                <td class="label">Timestamp</td>
                <td class="value">{now}</td>
            </tr>
        </table>
        <div class="notice">
            <p><strong>Unrecognised activity?</strong> If you did not attempt to sign in,
            change your password immediately and contact support.</p>
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Login verification — HagoCapitals", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# Password reset
# ─────────────────────────────────────────────────────────────────────────────

def send_password_reset_email(user, token: str, uid: str) -> bool:
    frontend   = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend}/reset-password?uid={uid}&token={token}"
    name       = user.first_name or "Trader"

    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Reset your password</div>
        <div class="text">
            We received a request to reset the password for your HagoCapitals account.
            Click the button below to choose a new password. This link expires in
            <strong>1 hour</strong>.
        </div>
        <div style="text-align:center; margin:32px 0;">
            <a href="{reset_link}" class="btn">Reset Password</a>
        </div>
        <div class="text" style="font-size:13px; color:#8fa896;">
            If the button doesn't work, copy and paste the link below into your browser:
        </div>
        <div class="link-fallback">{reset_link}</div>
        <div class="notice">
            <p><strong>Didn't request this?</strong> If you did not initiate a password
            reset, no action is needed. Your current password remains unchanged.</p>
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Password reset — HagoCapitals", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# Password changed confirmation
# ─────────────────────────────────────────────────────────────────────────────

def send_password_changed_email(user) -> bool:
    name = user.first_name or "Trader"
    now  = timezone.now().strftime("%b %d, %Y at %I:%M %p UTC")
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
  
    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Your password has been changed</div>
        <div class="text">
            This is a confirmation that the password for your HagoCapitals account was
            successfully updated on <strong>{now}</strong>.
        </div>
        <div class="notice">
            <p><strong>Wasn't you?</strong> If you did not make this change, please
            <a href="mailto:support@hagoscapitals.com" style="color:#B0D45A;">contact support</a>
            immediately to secure your account.</p>
        </div>
        <div class="divider"></div>
        <div class="text" style="font-size:13px; color:#8fa896;">
            All previously active sessions have been invalidated. Sign in again with
            your new password.
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Password changed — HagoCapitals", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# Admin notification design system — matches the shared "Citadels Market"
# admin-email layout 1:1 (dark header w/ wordmark, white info-row cards,
# dark footer) so these four templates look identical across sibling apps;
# only the wordmark and brand color differ here. Scoped to just these four
# functions — every other email in this file keeps its existing look.
# ─────────────────────────────────────────────────────────────────────────────

_ADMIN_BRAND         = "#06811d"   # HagoCapitals green
_ADMIN_HEADER_BG     = "#0d1117"
_ADMIN_BODY_BG       = "#f0f2f5"
_ADMIN_CARD_BG       = "#ffffff"
_ADMIN_TEXT_PRIMARY  = "#111827"
_ADMIN_TEXT_MUTED    = "#6b7280"
_ADMIN_BORDER        = "#e5e7eb"
_ADMIN_ACCENT_LIGHT  = "#eafaf0"


def _admin_base_styles():
    return f"""
        <style>
            @media only screen and (max-width: 600px) {{
                .email-container {{ width: 100% !important; }}
                .content-padding {{ padding: 24px 16px !important; }}
                .header-padding {{ padding: 32px 16px !important; }}
            }}
            body {{
                margin: 0; padding: 0;
                background-color: {_ADMIN_BODY_BG};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }}
            table {{ border-collapse: collapse; }}
            img {{ border: 0; display: block; }}
            a {{ color: {_ADMIN_BRAND}; text-decoration: none; }}
            .preheader {{
                display: none !important; visibility: hidden; mso-hide: all;
                font-size: 1px; line-height: 1px; max-height: 0; max-width: 0;
                opacity: 0; overflow: hidden;
            }}
        </style>
    """


def _admin_header(title, subtitle="", preheader=""):
    subtitle_html = f'<p style="margin:8px 0 0; font-size:14px; color:#9ca3af; font-weight:400; letter-spacing:0.5px;">{subtitle}</p>' if subtitle else ""
    pre = f'<span class="preheader">{preheader}</span>' if preheader else ""
    return f"""
    {pre}
    <tr>
      <td align="center" style="background-color:{_ADMIN_HEADER_BG}; padding:0;">
        <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td class="header-padding" style="padding:40px 40px 36px;">
              <table cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td>
                    <table cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background-color:{_ADMIN_BRAND}; border-radius:6px; width:8px; height:28px;">&nbsp;</td>
                        <td style="padding-left:10px; vertical-align:middle;">
                          <span style="font-size:18px; font-weight:700; color:#ffffff; letter-spacing:-0.3px;">HAGO</span>
                          <span style="font-size:18px; font-weight:300; color:{_ADMIN_BRAND}; letter-spacing:-0.3px;">&nbsp;CAPITALS</span>
                          <span style="font-size:11px; font-weight:500; color:#6b7280; letter-spacing:2px; display:block; margin-top:1px;">COPY TRADING PLATFORM</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td align="right" valign="middle">
                    <span style="font-size:11px; color:#374151; background-color:#1f2937; padding:4px 10px; border-radius:20px; letter-spacing:1px; font-weight:600;">SECURE</span>
                  </td>
                </tr>
              </table>
              <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:28px;">
                <tr><td style="height:1px; background:linear-gradient(to right, {_ADMIN_BRAND}, #064e1a, transparent);"></td></tr>
              </table>
              <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:28px;">
                <tr>
                  <td>
                    <p style="margin:0; font-size:26px; font-weight:700; color:#ffffff; line-height:1.2; letter-spacing:-0.5px;">{title}</p>
                    {subtitle_html}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def _admin_notif_footer():
    year = timezone.now().year
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    return f"""
    <tr>
      <td align="center" style="background-color:{_ADMIN_HEADER_BG}; padding:0;">
        <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="padding:32px 40px; border-top:1px solid #1f2937;">
              <table cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin:0 0 6px; font-size:13px; font-weight:600; color:#9ca3af; letter-spacing:1px;">HAGOCAPITALS</p>
                    <p style="margin:0 0 16px; font-size:11px; color:#4b5563;">Copy Trading Platform</p>
                    <table cellpadding="0" cellspacing="0" border="0" style="margin:0 auto 16px;">
                      <tr>
                        <td style="padding:0 10px;">
                          <a href="{frontend}/privacy-policy" style="font-size:11px; color:#6b7280; text-decoration:none;">Privacy Policy</a>
                        </td>
                        <td style="color:#374151; font-size:11px;">|</td>
                        <td style="padding:0 10px;">
                          <a href="{frontend}/terms" style="font-size:11px; color:#6b7280; text-decoration:none;">Terms of Service</a>
                        </td>
                      </tr>
                    </table>
                    <p style="margin:0; font-size:11px; color:#374151; line-height:1.6;">
                      &copy; {year} HagoCapitals. All rights reserved.<br>
                      This is an automated message &mdash; please do not reply directly to this email.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def _admin_info_row(label, value, value_color=None):
    color_style = f'color:{value_color}; font-weight:600;' if value_color else f'color:{_ADMIN_TEXT_PRIMARY};'
    return f"""
    <tr>
      <td style="padding:11px 0; border-bottom:1px solid {_ADMIN_BORDER}; font-size:13px; color:{_ADMIN_TEXT_MUTED}; width:42%; vertical-align:top;">{label}</td>
      <td style="padding:11px 0 11px 16px; border-bottom:1px solid {_ADMIN_BORDER}; font-size:13px; {color_style} text-align:right; word-break:break-all;">{value}</td>
    </tr>
    """


def _admin_section_heading(text, color=None):
    color = color or _ADMIN_BRAND
    return f'<p style="margin:0 0 12px; font-size:11px; font-weight:700; color:{color}; letter-spacing:1.5px; text-transform:uppercase;">{text}</p>'


def _admin_card(content, padding="24px 28px", border_left=None):
    border = f"border-left:3px solid {border_left};" if border_left else ""
    return f"""
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:{_ADMIN_CARD_BG}; border-radius:8px; {border} margin-bottom:16px;">
      <tr><td style="padding:{padding};">{content}</td></tr>
    </table>
    """


def _admin_wallet_card(wallet, heading="Pay Into This Wallet"):
    """Info card showing the admin's own deposit wallet — type, network, and
    full address — so both staff and the email record itself always show
    exactly where the user was instructed to send funds."""
    if not wallet:
        return ""
    addr_html = (
        f'<span style="font-family: Courier New, monospace; font-size:12px;">'
        f'{escape(wallet.address)}</span>'
    )
    return _admin_card(f'''
    {_admin_section_heading(heading, "#b45309")}
    <table cellpadding="0" cellspacing="0" border="0" width="100%">
        {_admin_info_row("Wallet Type", escape(wallet.get_name_display()))}
        {_admin_info_row("Network", escape(wallet.network or wallet.symbol))}
        {_admin_info_row("Address", addr_html)}
    </table>
    ''', border_left="#b45309")


# ─────────────────────────────────────────────────────────────────────────────
# Admin: payment intent notification
# ─────────────────────────────────────────────────────────────────────────────

def send_admin_payment_intent_notification(user, currency: str, dollar_amount, currency_unit, wallet=None) -> bool:
    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", settings.EMAIL_HOST_USER)
    subject = f"[DEPOSIT INTENT] {user.email} — ${dollar_amount}"
    timestamp = timezone.now().strftime("%B %d, %Y at %I:%M %p UTC")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{subject}</title>
      {_admin_base_styles()}
    </head>
    <body>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG}; padding:32px 0;">
      <tr><td align="center">
        <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG};">

          {_admin_header("Deposit Intent Initiated", "A user has entered a deposit amount.", "A user is about to make a deposit.")}

          <tr>
            <td align="center" style="background-color:{_ADMIN_BODY_BG}; padding:0;">
              <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="content-padding" style="padding:32px 40px;">

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_ADMIN_HEADER_BG}; border-radius:10px; margin-bottom:16px; border-left:4px solid {_ADMIN_BRAND};">
                      <tr>
                        <td style="padding:28px 32px;">
                          <p style="margin:0 0 4px; font-size:11px; font-weight:600; color:#6b7280; letter-spacing:1.5px; text-transform:uppercase;">Intended Deposit Amount</p>
                          <p style="margin:0 0 6px; font-size:40px; font-weight:700; color:{_ADMIN_BRAND}; line-height:1.1;">${dollar_amount}</p>
                          <p style="margin:0; font-size:14px; color:#9ca3af;">{currency_unit} {currency}</p>
                        </td>
                        <td align="right" valign="middle" style="padding:28px 32px;">
                          <span style="display:inline-block; background-color:{_ADMIN_ACCENT_LIGHT}; color:#065f27; font-size:11px; font-weight:700; padding:6px 14px; border-radius:20px; letter-spacing:0.5px;">INTENT</span>
                        </td>
                      </tr>
                    </table>

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_ADMIN_ACCENT_LIGHT}; border:1px solid #a7e8c0; border-radius:8px; margin-bottom:16px;">
                      <tr>
                        <td style="padding:14px 20px;">
                          <p style="margin:0; font-size:13px; color:#065f27; line-height:1.6;">
                            &#128276; The user has proceeded past Stage 1. A receipt upload is expected shortly. The transaction record will be created upon receipt submission.
                          </p>
                        </td>
                      </tr>
                    </table>

                    {_admin_card(f'''
                    {_admin_section_heading("Deposit Details")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Currency", escape(currency))}
                      {_admin_info_row("Crypto Units", f"{currency_unit} {currency}")}
                      {_admin_info_row("Initiated At", timestamp)}
                      {_admin_info_row("Receipt", '<span style="color:#9ca3af;">Pending upload (Stage 2)</span>')}
                    </table>
                    ''', border_left=_ADMIN_BRAND)}

                    {_admin_wallet_card(wallet)}

                    {_admin_card(f'''
                    {_admin_section_heading("Account Holder", "#3b82f6")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Full Name", f"{user.first_name} {user.last_name}")}
                      {_admin_info_row("Email", user.email)}
                      {_admin_info_row("User ID", f"#{user.id}")}
                      {_admin_info_row("Current Balance", f"${user.balance}")}
                    </table>
                    ''', border_left="#3b82f6")}

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {_admin_notif_footer()}

        </table>
      </td></tr>
    </table>
    </body>
    </html>
    """
    return send_email(admin_email, subject, html_content)


# ─────────────────────────────────────────────────────────────────────────────
# Admin: deposit notification
# ─────────────────────────────────────────────────────────────────────────────

def send_admin_deposit_notification(user, transaction, wallet=None) -> bool:
    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", settings.EMAIL_HOST_USER)
    tx_date = transaction.created_at.strftime("%B %d, %Y at %I:%M %p UTC")

    units_val = float(transaction.units or 0)
    amount_usd_val = float(transaction.amount_usd or 0)
    units_str = (
        f"{units_val:.8f}".rstrip("0").rstrip(".")
        if units_val > 0 and abs(units_val - amount_usd_val) > 0.0001
        else str(transaction.amount_usd)
    )
    crypto_row = (
        _admin_info_row("Crypto Amount", f"{units_str} {transaction.asset}", _ADMIN_BRAND)
        if units_val > 0 and abs(units_val - amount_usd_val) > 0.0001
        else ""
    )
    receipt_html = (
        f'<a href="{transaction.receipt.url}" target="_blank" style="color:{_ADMIN_BRAND}; font-weight:600;">View Receipt &rarr;</a>'
        if transaction.receipt else '<span style="color:#9ca3af;">Not uploaded</span>'
    )

    subject = f"[DEPOSIT] {user.email} — ${transaction.amount_usd:,.2f} ({units_str} {transaction.asset})"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{subject}</title>
      {_admin_base_styles()}
    </head>
    <body>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG}; padding:32px 0;">
      <tr><td align="center">
        <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG};">

          {_admin_header("New Deposit Request", "Action required &mdash; pending approval.", "A deposit is awaiting your review.")}

          <tr>
            <td align="center" style="background-color:{_ADMIN_BODY_BG}; padding:0;">
              <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="content-padding" style="padding:32px 40px;">

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_ADMIN_HEADER_BG}; border-radius:10px; margin-bottom:16px; border-left:4px solid {_ADMIN_BRAND};">
                      <tr>
                        <td style="padding:28px 32px;">
                          <p style="margin:0 0 4px; font-size:11px; font-weight:600; color:#6b7280; letter-spacing:1.5px; text-transform:uppercase;">Deposit Amount</p>
                          <p style="margin:0 0 6px; font-size:40px; font-weight:700; color:{_ADMIN_BRAND}; line-height:1.1;">${transaction.amount_usd:,.2f}</p>
                          <p style="margin:0; font-size:14px; color:#9ca3af;">{units_str} {transaction.asset}</p>
                        </td>
                        <td align="right" valign="middle" style="padding:28px 32px;">
                          <span style="display:inline-block; background-color:#fef3c7; color:#b45309; font-size:11px; font-weight:700; padding:6px 14px; border-radius:20px; letter-spacing:0.5px;">PENDING</span>
                        </td>
                      </tr>
                    </table>

                    {_admin_card(f'''
                    {_admin_section_heading("Transaction Details")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Reference", transaction.tx_id)}
                      {_admin_info_row("Date &amp; Time", tx_date)}
                      {_admin_info_row("Asset", transaction.asset)}
                      {crypto_row}
                      {_admin_info_row("Receipt", receipt_html)}
                    </table>
                    ''', border_left=_ADMIN_BRAND)}

                    {_admin_wallet_card(wallet, heading="User Paid Into This Wallet")}

                    {_admin_card(f'''
                    {_admin_section_heading("Account Holder", "#3b82f6")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Full Name", f"{user.first_name} {user.last_name}")}
                      {_admin_info_row("Email", user.email)}
                      {_admin_info_row("User ID", f"#{user.id}")}
                      {_admin_info_row("Current Balance", f"${user.balance:,.2f}")}
                    </table>
                    ''', border_left="#3b82f6")}

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#fffbeb; border:1px solid #fcd34d; border-radius:8px; margin-bottom:24px;">
                      <tr>
                        <td style="padding:16px 20px;">
                          <p style="margin:0; font-size:13px; color:#78350f; line-height:1.6;">
                            <strong>&#9888; Action Required:</strong> Please log in to the admin dashboard to review the payment receipt and update the transaction status accordingly.
                          </p>
                        </td>
                      </tr>
                    </table>

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {_admin_notif_footer()}

        </table>
      </td></tr>
    </table>
    </body>
    </html>
    """
    return send_email(admin_email, subject, html_content)


# ─────────────────────────────────────────────────────────────────────────────
# Admin: withdrawal notification
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# User: deposit confirmation
# ─────────────────────────────────────────────────────────────────────────────

def send_user_deposit_confirmation(user, transaction, wallet_name: str = "") -> bool:
    name     = user.first_name or "Trader"
    tx_date  = transaction.created_at.strftime("%b %d, %Y at %I:%M %p UTC")
    asset_label = transaction.asset + (f" ({wallet_name})" if wallet_name else "")
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Deposit Request Received</div>
        <div class="text">
            We've received your deposit request and it is now under review.
            You will be notified once it has been approved and credited to your account.
        </div>
        <div class="amount-box deposit">
            <div class="amount">${transaction.amount_usd}</div>
            <div class="amount-label">Deposit Amount (USD)</div>
        </div>
        <div class="section-title">Request Details</div>
        <table class="detail-table">
            <tr>
                <td class="label">Reference</td>
                <td class="value" style="font-size:12px;font-family:monospace;">{transaction.tx_id}</td>
            </tr>
            <tr><td class="label">Asset</td><td class="value">{asset_label}</td></tr>
            <tr>
                <td class="label">Status</td>
                <td class="value"><span class="badge badge-pending">Pending</span></td>
            </tr>
            <tr><td class="label">Date</td><td class="value">{tx_date}</td></tr>
        </table>
        <div class="notice">
            <p>Deposits are typically reviewed within <strong>24–48 hours</strong>.
            If you have any questions, please contact our support team.</p>
        </div>
        <div style="text-align:center; margin:28px 0;">
            <a href="{frontend}/transactions" class="btn">View Transaction</a>
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Deposit Request Received — HagoCapitals", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# User: abandoned-deposit reminder
# ─────────────────────────────────────────────────────────────────────────────

def send_deposit_reminder_email(user, intent) -> bool:
    """Sent by the send_deposit_reminders management command when a
    DepositIntent has sat uncompleted past the reminder delay — nudges the
    user to come back and finish the deposit they started."""
    name     = user.first_name or "Trader"
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Did life get in the way?</div>
        <div class="text">
            We noticed you started a deposit but haven't completed it yet.
            Don't let it slip — finish funding your account so your capital
            can start working for you.
        </div>
        <div class="amount-box neutral">
            <div class="amount">${intent.amount_usd}</div>
            <div class="amount-label">{intent.asset} deposit awaiting completion</div>
        </div>
        <div class="notice">
            <p>Nothing has been charged yet — this deposit was never submitted,
            so there's nothing to cancel. It only takes a minute to finish.</p>
        </div>
        <div style="text-align:center; margin:28px 0;">
            <a href="{frontend}/dashboard" class="btn">Complete Your Deposit</a>
        </div>
        <div class="text" style="font-size:13px;">
            If you ran into any issues, reply to this email and our support
            team will help you get it sorted.
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Don't miss out — complete your deposit", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# User: withdrawal confirmation
# ─────────────────────────────────────────────────────────────────────────────

def send_user_withdrawal_confirmation(user, transaction, wallet_name: str = "") -> bool:
    name     = user.first_name or "Trader"
    tx_date  = transaction.created_at.strftime("%b %d, %Y at %I:%M %p UTC")
    asset_label = transaction.asset + (f" ({wallet_name})" if wallet_name else "")
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    # Full address (not masked) — the user needs to be able to verify the
    # exact destination they submitted, and this email is only ever sent to
    # that same user.
    addr = escape(transaction.wallet_address or "")

    destination_row = (
        f'<tr><td class="label">Destination</td>'
        f'<td class="value" style="font-size:12px;font-family:monospace;word-break:break-all;">{addr}</td></tr>'
        if addr else ""
    )

    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Withdrawal Request Submitted</div>
        <div class="text">
            Your withdrawal request has been submitted and is pending approval.
            The requested amount has been reserved from your account balance.
        </div>
        <div class="amount-box withdraw">
            <div class="amount">${transaction.amount_usd}</div>
            <div class="amount-label">Withdrawal Amount (USD)</div>
        </div>
        <div class="section-title">Request Details</div>
        <table class="detail-table">
            <tr>
                <td class="label">Reference</td>
                <td class="value" style="font-size:12px;font-family:monospace;">{transaction.tx_id}</td>
            </tr>
            <tr><td class="label">Asset</td><td class="value">{asset_label}</td></tr>
            {destination_row}
            <tr>
                <td class="label">Status</td>
                <td class="value"><span class="badge badge-pending">Pending</span></td>
            </tr>
            <tr><td class="label">Date</td><td class="value">{tx_date}</td></tr>
        </table>
        <div class="notice">
            <p>Withdrawals are typically processed within <strong>24–48 hours</strong> after admin
            approval. If you did not initiate this request, please contact support immediately.</p>
        </div>
        <div style="text-align:center; margin:28px 0;">
            <a href="{frontend}/transactions" class="btn">View Transaction</a>
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Withdrawal Request Submitted — HagoCapitals", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# Admin: withdrawal intent notification
# ─────────────────────────────────────────────────────────────────────────────

def send_admin_withdrawal_intent_notification(user, currency: str, dollar_amount, withdraw_from: str, address: str) -> bool:
    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", settings.EMAIL_HOST_USER)
    timestamp = timezone.now().strftime("%B %d, %Y at %I:%M %p UTC")
    # `address` is raw, unvalidated user input straight from the request body —
    # escape it before embedding in HTML so it can't inject markup into the
    # admin's inbox. Shown in full (not truncated/masked) so staff can copy
    # the exact destination for payout.
    address_html = f'<span style="font-family: Courier New, monospace; font-size:12px;">{escape(address or "")}</span>'

    subject = f"[WITHDRAWAL INTENT] {user.email} — ${dollar_amount}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{subject}</title>
      {_admin_base_styles()}
    </head>
    <body>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG}; padding:32px 0;">
      <tr><td align="center">
        <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG};">

          {_admin_header("Withdrawal Intent Initiated", "A user has clicked Confirm Withdrawal.", "A user is about to make a withdrawal.")}

          <tr>
            <td align="center" style="background-color:{_ADMIN_BODY_BG}; padding:0;">
              <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="content-padding" style="padding:32px 40px;">

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_ADMIN_HEADER_BG}; border-radius:10px; margin-bottom:16px; border-left:4px solid #ef4444;">
                      <tr>
                        <td style="padding:28px 32px;">
                          <p style="margin:0 0 4px; font-size:11px; font-weight:600; color:#6b7280; letter-spacing:1.5px; text-transform:uppercase;">Intended Withdrawal Amount</p>
                          <p style="margin:0 0 6px; font-size:40px; font-weight:700; color:#ef4444; line-height:1.1;">${dollar_amount}</p>
                          <p style="margin:0; font-size:14px; color:#9ca3af;">{withdraw_from} &middot; {currency}</p>
                        </td>
                        <td align="right" valign="middle" style="padding:28px 32px;">
                          <span style="display:inline-block; background-color:{_ADMIN_ACCENT_LIGHT}; color:#065f27; font-size:11px; font-weight:700; padding:6px 14px; border-radius:20px; letter-spacing:0.5px;">INTENT</span>
                        </td>
                      </tr>
                    </table>

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_ADMIN_ACCENT_LIGHT}; border:1px solid #a7e8c0; border-radius:8px; margin-bottom:16px;">
                      <tr>
                        <td style="padding:14px 20px;">
                          <p style="margin:0; font-size:13px; color:#065f27; line-height:1.6;">
                            &#128276; This is an early signal, not a confirmed withdrawal &mdash; a separate notification follows once the request is recorded. Follow up if that confirmation never arrives.
                          </p>
                        </td>
                      </tr>
                    </table>

                    {_admin_card(f'''
                    {_admin_section_heading("Withdrawal Details", "#ef4444")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Withdraw From", withdraw_from)}
                      {_admin_info_row("Amount (USD)", f"${dollar_amount}", "#ef4444")}
                      {_admin_info_row("Wallet Type / Currency", escape(currency))}
                      {_admin_info_row("Destination Address", address_html)}
                      {_admin_info_row("Initiated At", timestamp)}
                    </table>
                    ''', border_left="#ef4444")}

                    {_admin_card(f'''
                    {_admin_section_heading("Account Holder", "#3b82f6")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Full Name", f"{user.first_name} {user.last_name}")}
                      {_admin_info_row("Email", user.email)}
                      {_admin_info_row("User ID", f"#{user.id}")}
                      {_admin_info_row("Current Balance", f"${user.balance}")}
                    </table>
                    ''', border_left="#3b82f6")}

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {_admin_notif_footer()}

        </table>
      </td></tr>
    </table>
    </body>
    </html>
    """
    return send_email(admin_email, subject, html_content)


# ─────────────────────────────────────────────────────────────────────────────
# Admin: withdrawal notification
# ─────────────────────────────────────────────────────────────────────────────

def send_admin_withdrawal_notification(user, transaction, payment_method=None) -> bool:
    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", settings.EMAIL_HOST_USER)
    tx_date = transaction.created_at.strftime("%B %d, %Y at %I:%M %p UTC") if hasattr(transaction, "created_at") else "—"

    method_type = escape(getattr(payment_method, "method_type", "Not specified") if payment_method else "Not specified")
    payment_address = "N/A"
    if payment_method:
        payment_address = (
            getattr(payment_method, "address", None)
            or getattr(payment_method, "bank_account_number", None)
            or "N/A"
        )
    # Shown in full (not truncated/masked) — staff need the exact destination
    # to process the payout — and escaped since it's user-supplied.
    payment_addr_html = f'<span style="font-family: Courier New, monospace; font-size:12px;">{escape(payment_address)}</span>'

    bank_row = (
        _admin_info_row("Bank Name", escape(payment_method.bank_name))
        if payment_method and getattr(payment_method, "bank_name", None) else ""
    )

    subject = f"[WITHDRAWAL] {user.email} — ${transaction.amount_usd}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{subject}</title>
      {_admin_base_styles()}
    </head>
    <body>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG}; padding:32px 0;">
      <tr><td align="center">
        <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0" style="background-color:{_ADMIN_BODY_BG};">

          {_admin_header("Withdrawal Request", "Urgent &mdash; user balance has been deducted.", "A withdrawal is awaiting processing.")}

          <tr>
            <td align="center" style="background-color:{_ADMIN_BODY_BG}; padding:0;">
              <table width="600" class="email-container" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="content-padding" style="padding:32px 40px;">

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_ADMIN_HEADER_BG}; border-radius:10px; margin-bottom:16px; border-left:4px solid #ef4444;">
                      <tr>
                        <td style="padding:28px 32px;">
                          <p style="margin:0 0 4px; font-size:11px; font-weight:600; color:#6b7280; letter-spacing:1.5px; text-transform:uppercase;">Withdrawal Amount</p>
                          <p style="margin:0 0 6px; font-size:40px; font-weight:700; color:#ef4444; line-height:1.1;">${transaction.amount_usd}</p>
                          <p style="margin:0; font-size:14px; color:#9ca3af;">Balance after deduction: <strong style="color:#f9fafb;">${user.balance}</strong></p>
                        </td>
                        <td align="right" valign="middle" style="padding:28px 32px;">
                          <span style="display:inline-block; background-color:#fee2e2; color:#b91c1c; font-size:11px; font-weight:700; padding:6px 14px; border-radius:20px; letter-spacing:0.5px;">PENDING</span>
                        </td>
                      </tr>
                    </table>

                    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#fff1f2; border:1px solid #fda4af; border-radius:8px; margin-bottom:16px;">
                      <tr>
                        <td style="padding:16px 20px;">
                          <p style="margin:0; font-size:13px; color:#9f1239; line-height:1.6;">
                            <strong>&#128680; Urgent:</strong> The user's balance has already been deducted. Please process this withdrawal promptly, or reverse the transaction if unable to complete.
                          </p>
                        </td>
                      </tr>
                    </table>

                    {_admin_card(f'''
                    {_admin_section_heading("Transaction Details", "#ef4444")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Reference", transaction.tx_id)}
                      {_admin_info_row("Date &amp; Time", tx_date)}
                      {_admin_info_row("Amount", f"${transaction.amount_usd}", "#ef4444")}
                    </table>
                    ''', border_left="#ef4444")}

                    {_admin_card(f'''
                    {_admin_section_heading("Account Holder", "#3b82f6")}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Full Name", f"{user.first_name} {user.last_name}")}
                      {_admin_info_row("Email", user.email)}
                      {_admin_info_row("User ID", f"#{user.id}")}
                      {_admin_info_row("Remaining Balance", f"${user.balance}")}
                    </table>
                    ''', border_left="#3b82f6")}

                    {_admin_card(f'''
                    {_admin_section_heading("Payment Destination", _ADMIN_BRAND)}
                    <table cellpadding="0" cellspacing="0" border="0" width="100%">
                      {_admin_info_row("Wallet Type", method_type)}
                      {_admin_info_row("Address / Account", payment_addr_html)}
                      {bank_row}
                    </table>
                    ''', border_left=_ADMIN_BRAND)}

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {_admin_notif_footer()}

        </table>
      </td></tr>
    </table>
    </body>
    </html>
    """
    return send_email(admin_email, subject, html_content)


# ─────────────────────────────────────────────────────────────────────────────
# User: deposit approved
# ─────────────────────────────────────────────────────────────────────────────

def send_user_deposit_approved_email(user, transaction) -> bool:
    name     = user.first_name or "Trader"
    tx_date  = transaction.created_at.strftime("%b %d, %Y at %I:%M %p UTC")
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        <div class="heading">Deposit Approved &amp; Credited</div>
        <div class="text">
            Great news! Your deposit has been reviewed and approved.
            The amount has been credited to your HagoCapitals account and is ready to use.
        </div>
        <div class="amount-box deposit">
            <div class="amount">${transaction.amount_usd:,.2f}</div>
            <div class="amount-label">Amount Credited (USD)</div>
        </div>
        <div class="section-title">Transaction Details</div>
        <table class="detail-table">
            <tr>
                <td class="label">Reference</td>
                <td class="value" style="font-size:12px;font-family:monospace;">{transaction.tx_id}</td>
            </tr>
            <tr><td class="label">Asset</td><td class="value">{transaction.asset}</td></tr>
            <tr>
                <td class="label">Status</td>
                <td class="value"><span class="badge badge-success">Completed</span></td>
            </tr>
            <tr><td class="label">Date</td><td class="value">{tx_date}</td></tr>
        </table>
        <div class="notice">
            <p>Your new account balance reflects this deposit. You can now use your funds to copy traders and grow your portfolio.</p>
        </div>
        <div style="text-align:center; margin:28px 0;">
            <a href="{frontend}/transactions" class="btn">View Transactions</a>
        </div>
    </div>
    {_signature_html()}
    {_footer_html(user.email)}
    """
    return send_email(user.email, "Deposit Approved — Funds Credited to Your Account", _wrap(body))


# ─────────────────────────────────────────────────────────────────────────────
# Admin: custom / bulk client email
# ─────────────────────────────────────────────────────────────────────────────
# Composed from the admin panel (dashboard app) and sent to one or many users
# at once. Reuses the exact same header/footer/button styling as every other
# email above — only the heading, message body, optional CTA button, and
# footer social icons change per campaign.
# ─────────────────────────────────────────────────────────────────────────────

def _build_custom_email_html(
    name: str,
    email: str,
    message: str,
    heading: str = "",
    social_links: dict | None = None,
    cta_text: str = "",
    cta_url: str = "",
) -> str:
    """
    Build the full HTML document for a custom email, shared by `send_custom_email`
    (real send) and `render_custom_email_preview` (admin preview, not sent).

    - `message` is plain text; blank lines start a new paragraph, single
      newlines become <br>. It is HTML-escaped, so admins can't break markup.
    - `heading` is optional — omitted entirely if blank.
    - `social_links` is an optional dict like {"facebook": "https://...", ...}.
      Only platforms with a non-empty URL get an icon; if none are set (or
      the dict is empty/None), no social row is rendered at all.
    - `cta_text` + `cta_url` are optional — both must be set to show a button.
    """
    message_html = linebreaks(message.strip(), autoescape=True)

    cta_block = ""
    if cta_text and cta_url:
        cta_block = f"""
        <div style="text-align:center; margin:32px 0;">
            <a href="{escape(cta_url)}" class="btn">{escape(cta_text)}</a>
        </div>"""

    heading_block = f'<div class="heading">{escape(heading)}</div>' if heading else ""

    body = f"""
    {_header_html()}
    <div class="body-content">
        <div class="greeting">Hello {name},</div>
        {heading_block}
        <div class="text">{message_html}</div>
        {cta_block}
    </div>
    {_signature_html()}
    {_footer_html(email, social_links)}
    """
    return _wrap(body)


def send_custom_email(
    user,
    subject: str,
    message: str,
    heading: str = "",
    social_links: dict | None = None,
    cta_text: str = "",
    cta_url: str = "",
) -> bool:
    """Send an admin-composed email to a single user using the HagoCapitals template."""
    name = user.first_name or "Trader"
    html = _build_custom_email_html(name, user.email, message, heading, social_links, cta_text, cta_url)
    return send_email(user.email, subject, html)


# Resend's batch endpoint accepts at most 100 emails per call.
BATCH_CHUNK_SIZE = 100


def send_custom_email_batch(
    users,
    subject: str,
    message: str,
    heading: str = "",
    social_links: dict | None = None,
    cta_text: str = "",
    cta_url: str = "",
) -> dict:
    """
    Send an admin-composed email to many users at once via Resend's Batch API
    (POST /emails/batch). A whole chunk of up to 100 recipients counts as a
    single request against Resend's rate limit, instead of one request per
    recipient — the per-recipient loop this replaces was prone to tripping
    that limit (and failing silently) on larger campaigns.

    Returns {user.id: bool} — True if that recipient's email was accepted.
    """
    results: dict = {}
    users = list(users)

    for i in range(0, len(users), BATCH_CHUNK_SIZE):
        chunk = users[i : i + BATCH_CHUNK_SIZE]
        payload = [
            {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [user.email],
                "subject": subject,
                "html": _build_custom_email_html(
                    user.first_name or "Trader", user.email, message, heading, social_links, cta_text, cta_url
                ),
            }
            for user in chunk
        ]
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Batch.send(payload)
            for user in chunk:
                results[user.id] = True
            logger.info(f"Batch-sent custom email to {len(chunk)} recipient(s)")
        except Exception as e:
            logger.error(f"Batch send failed for {len(chunk)} recipient(s): {str(e)}")
            for user in chunk:
                results[user.id] = False

        # Small gap between chunks — stays well clear of the rate limit even
        # though each chunk is already just one request.
        if i + BATCH_CHUNK_SIZE < len(users):
            time.sleep(0.15)

    return results


def render_custom_email_preview(
    message: str,
    heading: str = "",
    social_links: dict | None = None,
    cta_text: str = "",
    cta_url: str = "",
    preview_name: str = "Trader",
    preview_email: str = "client@example.com",
) -> str:
    """Render the exact HTML a recipient would receive, without sending — used for
    the admin panel's campaign detail/preview page."""
    return _build_custom_email_html(preview_name, preview_email, message, heading, social_links, cta_text, cta_url)
