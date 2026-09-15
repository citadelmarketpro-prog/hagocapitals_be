from django.urls import path
from .views import (
    AdminWalletListView,
    ChangePasswordView,
    CopyTradeListView,
    DashboardStatsView,
    LoyaltyTiersView,
    NewsListView,
    PortfolioBreakdownView,
    PortfolioChartView,
    TransferInfoView,
    TransferView,
    DepositView,
    DepositIntentView,
    WithdrawalIntentView,
    ForgotPasswordView,
    KycView,
    LoginView,
    LogoutView,
    MeView,
    NotificationDetailView,
    NotificationListView,
    NotificationReadAllView,
    PaymentMethodDeleteView,
    PaymentMethodListView,
    PaymentMethodUpsertView,
    RegisterView,
    ResetPasswordView,
    TokenRefreshView,
    CopyTraderView,
    TraderDetailView,
    TraderListView,
    TraderSimilarListView,
    TransactionListView,
    WithdrawalView,
)
from .referral_views import (
    ReferralInfoView,
    ReferralListView,
    ReferralGenerateView,
    ReferralValidateView,
)
from .wallet_views import WalletListView, WalletConnectView, WalletDisconnectView
from .signal_views import SignalListView, SignalPurchaseView, PurchasedSignalListView

urlpatterns = [
    path("register/",          RegisterView.as_view(),       name="auth-register"),
    path("login/",             LoginView.as_view(),           name="auth-login"),
    path("logout/",            LogoutView.as_view(),          name="auth-logout"),
    path("token/refresh/",     TokenRefreshView.as_view(),    name="auth-token-refresh"),
    path("me/",                MeView.as_view(),               name="auth-me"),
    path("kyc/",               KycView.as_view(),              name="auth-kyc"),
    path("password/forgot/",   ForgotPasswordView.as_view(),  name="auth-password-forgot"),
    path("password/reset/",    ResetPasswordView.as_view(),   name="auth-password-reset"),
    path("password/change/",   ChangePasswordView.as_view(),  name="auth-password-change"),

    # Notifications
    path("notifications/",           NotificationListView.as_view(),    name="notifications-list"),
    path("notifications/read-all/",  NotificationReadAllView.as_view(), name="notifications-read-all"),
    path("notifications/<int:pk>/",  NotificationDetailView.as_view(),  name="notifications-detail"),

    # Referral program
    path("referral/info/",     ReferralInfoView.as_view(),     name="referral-info"),
    path("referral/list/",     ReferralListView.as_view(),     name="referral-list"),
    path("referral/generate/", ReferralGenerateView.as_view(), name="referral-generate"),
    path("referral/validate/", ReferralValidateView.as_view(), name="referral-validate"),

    # Trading Signals
    path("signals/",                    SignalListView.as_view(),         name="signals-list"),
    path("signals/purchased/",          PurchasedSignalListView.as_view(), name="signals-purchased"),
    path("signals/<int:pk>/purchase/",  SignalPurchaseView.as_view(),      name="signals-purchase"),
]

# Wallet URLs — registered at /api/wallets/ in main urls.py
wallet_urlpatterns = [
    path("",                        WalletListView.as_view(),       name="wallets-list"),
    path("connect/",                WalletConnectView.as_view(),    name="wallets-connect"),
    path("<str:wallet_type>/disconnect/", WalletDisconnectView.as_view(), name="wallets-disconnect"),
]

# Transaction URLs — registered at /api/transactions/ in main urls.py
transaction_urlpatterns = [
    path("",            TransactionListView.as_view(),  name="transactions-list"),
    path("wallets/",    AdminWalletListView.as_view(),  name="transactions-wallets"),
    path("deposit/",    DepositView.as_view(),          name="transactions-deposit"),
    path("deposit-intent/", DepositIntentView.as_view(), name="transactions-deposit-intent"),
    path("withdraw/",   WithdrawalView.as_view(),       name="transactions-withdraw"),
    path("withdrawal-intent/", WithdrawalIntentView.as_view(), name="transactions-withdrawal-intent"),
]

# Dashboard URLs — registered at /api/dashboard/ in main urls.py
dashboard_urlpatterns = [
    path("stats/",                DashboardStatsView.as_view(),       name="dashboard-stats"),
    path("loyalty-tiers/",        LoyaltyTiersView.as_view(),         name="dashboard-loyalty-tiers"),
    path("copy-trades/",          CopyTradeListView.as_view(),         name="dashboard-copy-trades"),
    path("portfolio-breakdown/",  PortfolioBreakdownView.as_view(),    name="dashboard-portfolio-breakdown"),
    path("portfolio-chart/",      PortfolioChartView.as_view(),        name="dashboard-portfolio-chart"),
]

# Transfer URLs — registered at /api/transfer/ in main urls.py
transfer_urlpatterns = [
    path("info/",  TransferInfoView.as_view(), name="transfer-info"),
    path("",       TransferView.as_view(),     name="transfer"),
]

# Trader URLs — registered at /api/traders/ in main urls.py
trader_urlpatterns = [
    path("",                    TraderListView.as_view(),         name="traders-list"),
    path("<int:pk>/",           TraderDetailView.as_view(),       name="traders-detail"),
    path("<int:pk>/similar/",   TraderSimilarListView.as_view(),  name="traders-similar"),
    path("<int:pk>/copy/",      CopyTraderView.as_view(),         name="traders-copy"),
]

# Payment method URLs — registered at /api/payment-methods/ in main urls.py
payment_method_urlpatterns = [
    path("",                PaymentMethodListView.as_view(),   name="payment-methods-list"),
    path("save/",           PaymentMethodUpsertView.as_view(), name="payment-methods-save"),
    path("<int:wallet_id>/", PaymentMethodDeleteView.as_view(), name="payment-methods-delete"),
]
