from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UsernameField
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import PasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import re_path, reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

UserModel = get_user_model()


def _get_password_reset_token_expiry():
    if hasattr(settings, 'PASSWORD_RESET_TIMEOUT'):
        # Django 3.1+
        return settings.PASSWORD_RESET_TIMEOUT
    else:
        # Django 3.0-
        return settings.PASSWORD_RESET_TIMEOUT_DAYS


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username',)
        field_classes = {'username': UsernameField}

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs.update(
                {'autofocus': ''})

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.is_staff = True  # Non-staff users make no sense in our case
        user.set_unusable_password()
        return user


class ResetUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(ResetUserChangeForm, self).__init__(*args, **kwargs)
        # Override the help text, so there will be no 'change password' link
        self.fields['password'].help_text = _(
            'Raw passwords are not stored, so there is no way to see this '
            'user\'s password, but you can reset the password using '
            'the link on top of this form.')


class AdminResetCompleteView(PasswordResetCompleteView):
    def get_context_data(self, **kwargs):
        context = super(AdminResetCompleteView,
                        self).get_context_data(**kwargs)
        context['login_url'] = reverse('admin:login')
        return context


if UserModel.USERNAME_FIELD == 'email':
    PERSONAL_INFO_FIELDS = ('first_name', 'last_name')
    LIST_DISPLAY = (UserModel.USERNAME_FIELD, 'first_name', 'last_name',
                    'is_staff')
else:
    PERSONAL_INFO_FIELDS = ('first_name', 'last_name', 'email')
    LIST_DISPLAY = (UserModel.USERNAME_FIELD, 'email', 'first_name',
                    'last_name', 'is_staff')


class PasswordResetUserAdmin(UserAdmin):
    add_form = UserCreationForm
    add_form_template = 'admin/add_user_form.html'
    fieldsets = (
        (None, {'fields': (UserModel.USERNAME_FIELD, 'password')}),
        (_('Personal info'), {'fields': PERSONAL_INFO_FIELDS}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': [UserModel.USERNAME_FIELD] + list(
                UserModel.REQUIRED_FIELDS)
        }),
    )
    form = ResetUserChangeForm
    change_form_template = 'admin/change_user.html'
    list_display = LIST_DISPLAY
    ordering = (UserModel.USERNAME_FIELD,)

    def get_urls(self):
        return [
            re_path('^(?P<id>[^/.]+)/password_reset_url/$',
                    self.admin_site.admin_view(self.password_reset_url),
                    name='password_reset_url'),
            re_path(r'^password_reset_confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/'
                    r'(?P<token>[0-9A-Za-z]+-[0-9A-Za-z]+)/$',
                    PasswordResetConfirmView.as_view(
                        success_url=reverse_lazy(
                            'admin:password_reset_complete')),
                    name='password_reset_confirm'),
            re_path(r'^password_reset_complete/done/$',
                    AdminResetCompleteView.as_view(),
                    name='password_reset_complete')
        ] + super(PasswordResetUserAdmin, self).get_urls()

    @never_cache
    def password_reset_url(self, request, id, form_url=''):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = self.get_object(request, unquote(id))
        if user is None:
            raise Http404(_('%(name)s object with primary key %(key)r does '
                            'not exist.') % {
                'name': self.model._meta.verbose_name,
                'key': escape(id),
            })

        token_generator = PasswordResetTokenGenerator()
        url = reverse(
            'admin:password_reset_confirm',
            kwargs={'uidb64': force_str(
                urlsafe_base64_encode(force_bytes(user.pk))),
                'token': token_generator.make_token(user)})
        url = request.build_absolute_uri(url)
        return TemplateResponse(
            request,
            'admin/password_reset_url.html',
            context={'user': user, 'url': url, 'title': _('Password reset'),
                     'timeout_days': _get_password_reset_token_expiry()})


if admin.site.is_registered(UserModel):
    admin.site.unregister(UserModel)
admin.site.register(UserModel, PasswordResetUserAdmin)
