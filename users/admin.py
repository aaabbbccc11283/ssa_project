from django.contrib import admin
from .models import Profile, UserChangeLog

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname')
    search_fields = ('user__username', 'nickname')
    list_filter = ('nickname',)

class UserChangeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'field_name', 'old_value', 'new_value', 'timestamp')
    list_filter = ('field_name', 'timestamp')
    search_fields = ('user__username', 'field_name', 'old_value', 'new_value')

admin.site.register(Profile, ProfileAdmin)
admin.site.register(UserChangeLog, UserChangeLogAdmin)
