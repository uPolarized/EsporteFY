from django.db import connection

from app.models import UserConsentLog


def table_exists(table_name):
    try:
        return table_name in connection.introspection.table_names()
    except Exception:
        return False


def has_required_consents(user):
    if not table_exists(UserConsentLog._meta.db_table):
        return True

    required_types = [
        UserConsentLog.TYPE_TERMS,
        UserConsentLog.TYPE_PRIVACY,
    ]

    latest_by_type = {}
    logs = (
        UserConsentLog.objects.filter(user=user, consent_type__in=required_types)
        .order_by("consent_type", "-timestamp")
    )
    for log in logs:
        if log.consent_type not in latest_by_type:
            latest_by_type[log.consent_type] = log

    return all(
        latest_by_type.get(consent_type) and latest_by_type[consent_type].accepted
        for consent_type in required_types
    )
