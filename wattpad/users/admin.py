from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('selected_genres',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
