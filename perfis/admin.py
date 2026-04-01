from django.contrib import admin
from .models import AccountLoginEvent, UserPrivacySettings


@admin.register(UserPrivacySettings)
class UserPrivacySettingsAdmin(admin.ModelAdmin):
	list_display = ('user', 'show_profile_public', 'show_online_status', 'allow_friend_requests', 'two_factor_email_enabled', 'updated_at')
	search_fields = ('user__username', 'user__email')
	list_filter = ('show_profile_public', 'show_online_status', 'allow_friend_requests', 'two_factor_email_enabled')


@admin.register(AccountLoginEvent)
class AccountLoginEventAdmin(admin.ModelAdmin):
	list_display = ('user', 'login_method', 'ip_address', 'created_at')
	search_fields = ('user__username', 'user__email', 'ip_address', 'user_agent')
	list_filter = ('login_method', 'created_at')
