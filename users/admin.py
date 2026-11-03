from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import CustomUser


def titled(base, title):
    class Titled(base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title = title
    return Titled


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role_badge', 'status_badge', 'phone', 'date_joined']
    list_filter = [
        ('role', titled(admin.ChoicesFieldListFilter, 'Ролу')),
        ('is_verified', titled(admin.BooleanFieldListFilter, 'Текшерилген')),
        ('is_blocked', titled(admin.BooleanFieldListFilter, 'Бөгөттөлгөн')),
        ('is_active', titled(admin.BooleanFieldListFilter, 'Активдүү')),
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'university']
    ordering = ['-date_joined']
    list_per_page = 25
    actions = ['verify_users', 'unverify_users', 'block_users', 'unblock_users']

    fieldsets = UserAdmin.fieldsets + (
        ('Кошумча маалымат', {'fields': ('role', 'university', 'phone', 'profile_picture')}),
        ('Текшерүү статусу', {'fields': ('is_verified', 'is_blocked', 'verification_data')}),
        ('Жеке маалыматка макулдук', {'fields': ('consent_at',)}),
    )
    readonly_fields = ['consent_at']

    @admin.display(description='Ролу', ordering='role')
    def role_badge(self, obj):
        if obj.is_superuser:
            return format_html('<span class="{}">{}</span>', 'eh-badge eh-badge-dark', 'Админ')
        if obj.role == 'employer':
            return format_html('<span class="{}">{}</span>', 'eh-badge eh-badge-blue', 'Иш берүүчү')
        if obj.role == 'student':
            return format_html('<span class="{}">{}</span>', 'eh-badge eh-badge-gray', 'Студент')
        return '—'

    @admin.display(description='Статус')
    def status_badge(self, obj):
        if obj.is_blocked:
            return format_html('<span class="{}">{}</span>', 'eh-badge eh-badge-red', 'Бөгөттөлгөн')
        if obj.is_verified or obj.is_superuser:
            return format_html('<span class="{}">{}</span>', 'eh-badge eh-badge-green', 'Текшерилген')
        return format_html('<span class="{}">{}</span>', 'eh-badge eh-badge-yellow', 'Күтүүдө')

    @admin.action(description='Тандалгандарды ТЕКШЕРИЛГЕН деп белгилөө (тастыктоо)')
    def verify_users(self, request, queryset):
        n = queryset.update(is_verified=True)
        self.message_user(request, f'{n} колдонуучу тастыкталды.', messages.SUCCESS)

    @admin.action(description='Тастыктоону алып салуу')
    def unverify_users(self, request, queryset):
        n = queryset.exclude(pk=request.user.pk).update(is_verified=False)
        self.message_user(request, f'{n} колдонуучунун тастыгы алынды.', messages.WARNING)

    @admin.action(description='Тандалгандарды бөгөттөө')
    def block_users(self, request, queryset):
        n = queryset.exclude(pk=request.user.pk).update(is_blocked=True)
        self.message_user(request, f'{n} колдонуучу бөгөттөлдү.', messages.WARNING)

    @admin.action(description='Бөгөттөн чыгаруу')
    def unblock_users(self, request, queryset):
        n = queryset.update(is_blocked=False)
        self.message_user(request, f'{n} колдонуучу бөгөттөн чыгарылды.', messages.SUCCESS)


admin.site.register(CustomUser, CustomUserAdmin)
