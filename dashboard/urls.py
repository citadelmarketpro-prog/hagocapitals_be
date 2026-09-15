from django.urls import path
from . import views

app_name = "panel"

urlpatterns = [
    # Auth
    path("login/",   views.panel_login,  name="login"),
    path("logout/",  views.panel_logout, name="logout"),

    # Dashboard
    path("",         views.dashboard_home, name="dashboard"),

    # Users
    path("users/",                              views.user_list,        name="user_list"),
    path("users/create/",                       views.user_create,      name="user_create"),
    path("users/<int:pk>/",                     views.user_detail,      name="user_detail"),
    path("users/<int:pk>/edit/",                views.user_edit,        name="user_edit"),
    path("users/<int:pk>/delete/",              views.user_delete,      name="user_delete"),
    path("users/<int:pk>/toggle-transfer/",      views.user_toggle_transfer, name="user_toggle_transfer"),
    path("users/<int:pk>/approve-kyc/",         views.user_approve_kyc, name="user_approve_kyc"),
    path("users/<int:pk>/reject-kyc/",          views.user_reject_kyc,  name="user_reject_kyc"),
    path("users/<int:pk>/adjust-funds/",        views.user_adjust_funds,name="user_adjust_funds"),

    # Traders
    path("traders/",                                           views.trader_list,             name="trader_list"),
    path("traders/create/",                                    views.trader_create,           name="trader_create"),
    path("traders/<int:pk>/",                                  views.trader_detail,           name="trader_detail"),
    path("traders/<int:pk>/edit/",                             views.trader_edit,             name="trader_edit"),
    path("traders/<int:pk>/delete/",                           views.trader_delete,           name="trader_delete"),
    path("traders/<int:pk>/copiers/<int:copier_pk>/disconnect/", views.trader_disconnect_copier, name="trader_disconnect_copier"),

    # Requests: Deposits / Withdrawals / All Transactions
    path("requests/deposits/",           views.deposit_list,        name="deposit_list"),
    path("requests/withdrawals/",        views.withdrawal_list,     name="withdrawal_list"),
    path("transactions/",                views.transaction_list,    name="transaction_list"),
    path("transactions/<int:pk>/",       views.transaction_detail,  name="transaction_detail"),
    path("transactions/<int:pk>/approve/", views.transaction_approve, name="transaction_approve"),
    path("transactions/<int:pk>/reject/",  views.transaction_reject,  name="transaction_reject"),

    # Wallets
    path("wallets/",                views.wallet_list,   name="wallet_list"),
    path("wallets/create/",         views.wallet_create, name="wallet_create"),
    path("wallets/<int:pk>/edit/",  views.wallet_edit,   name="wallet_edit"),
    path("wallets/<int:pk>/delete/",views.wallet_delete, name="wallet_delete"),

    # Copy Trades
    path("copy-trades/",                                  views.copy_trade_list,          name="copy_trade_list"),
    path("copy-trades/<int:pk>/approve-cancel/",          views.copy_trade_approve_cancel, name="copy_trade_approve_cancel"),
    path("copy-trades/<int:pk>/reject-cancel/",           views.copy_trade_reject_cancel,  name="copy_trade_reject_cancel"),

    # FMP asset search API
    path("api/fmp-search/", views.panel_fmp_search, name="fmp_search"),

    # Investors
    path("investors/",                               views.investor_list,           name="investor_list"),
    path("investors/trades/",                        views.all_trade_records,       name="all_trade_records"),
    path("investors/<int:user_pk>/add-trade/",       views.investor_add_trade,      name="investor_add_trade"),
    path("investors/bulk-add-trade/",                views.investor_bulk_add_trade, name="investor_bulk_add_trade"),

    # Individual copy trade records
    path("investors/trades/<int:pk>/edit/",   views.copy_trade_record_edit,   name="copy_trade_record_edit"),
    path("investors/trades/<int:pk>/delete/", views.copy_trade_record_delete, name="copy_trade_record_delete"),

    # Custom / bulk client emails
    path("emails/",               views.custom_email_list,    name="custom_email_list"),
    path("emails/compose/",       views.custom_email_compose, name="custom_email_compose"),
    path("emails/history/",       views.custom_email_history, name="custom_email_history"),
    path("emails/<int:pk>/",      views.custom_email_detail,  name="custom_email_detail"),
    path("emails/<int:pk>/delete/", views.custom_email_delete, name="custom_email_delete"),

    # Signals (Trading Signals)
    path("signals/",               views.signal_list,   name="signal_list"),
    path("signals/create/",        views.signal_create, name="signal_create"),
    path("signals/<int:pk>/",      views.signal_detail, name="signal_detail"),
    path("signals/<int:pk>/edit/", views.signal_edit,   name="signal_edit"),
    path("signals/<int:pk>/delete/", views.signal_delete, name="signal_delete"),

    # Notifications
    path("notifications/",                  views.notification_list,   name="notification_list"),
    path("notifications/create/",           views.notification_create, name="notification_create"),
    path("notifications/<int:pk>/edit/",    views.notification_edit,   name="notification_edit"),
    path("notifications/<int:pk>/delete/",  views.notification_delete, name="notification_delete"),

    # Settings — User Cards
    path("cards/",                views.card_list,   name="card_list"),
    path("cards/<int:pk>/",       views.card_detail, name="card_detail"),
    path("cards/<int:pk>/edit/",  views.card_edit,   name="card_edit"),
    path("cards/<int:pk>/delete/", views.card_delete, name="card_delete"),

    # Settings — Change User Password
    path("settings/change-password/", views.change_user_password, name="change_user_password"),
]
