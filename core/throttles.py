from rest_framework.throttling import ScopedRateThrottle


class RegisterRateThrottle(ScopedRateThrottle):
    """Per-IP limit on account creation — see DEFAULT_THROTTLE_RATES["register"]
    in settings. Keeps a scripted signup bot from creating dozens of accounts
    even if it rotates through disposable email domains."""
    scope = "register"
