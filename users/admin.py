from django.contrib import admin
from .models import CustomUser, Community, Profile, Notifications, Report, RevenueSharingRule, SubscriptionPlan, Subscription
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group, User
from django.contrib.admin import AdminSite


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password Confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('name', 'username', 'email', 'phone', 'country', 'state', 'city', 'address', 'age',)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords Do Not Match')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.verification_code = CustomUser.objects.make_random_password()
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = ('name', 'username', 'email', 'password', 'phone', 'country', 'state', 'city', 'address', 'age', 'is_active', 'is_admin')

    def clean_password(self):
        return self.initial['password']


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('email', 'date_of_birth', 'is_admin', 'is_active', 'has_perm',)
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'username', )}),
        ('Personal info', {'fields': ('first_name',)}),
        ('Permissions', {'fields': ('is_admin', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = [
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'username', 'email', 'phone', 'country', 'state', 'city', 'address', 'age', 'password1', 'password2')
        }
        )
    ]
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class FlatPageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('url', 'title', 'content', 'sites')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('registration_required', 'template_name'),
        }),
    )


admin.site.site_header = 'Gospeller Administrations Dashboard'
admin.site.site_title = 'Gospeller Administrations'

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Profile)
admin.site.unregister(Group)
admin.site.register(Notifications)
admin.site.register(SubscriptionPlan)
admin.site.register(Report)
admin.site.register(RevenueSharingRule)
admin.site.register(Community)
admin.site.register(Subscription)


