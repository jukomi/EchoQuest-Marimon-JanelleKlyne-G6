from datetime import timedelta
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import User

MAX_FAILED = 5
LOCK_MINUTES = 15


class StyledFormMixin:
    def style_fields(self):
        for f in self.fields.values():
            if isinstance(f.widget, forms.CheckboxInput):
                f.widget.attrs['class'] = 'form-check-input'
            else:
                f.widget.attrs['class'] = 'form-control'


class RegisterForm(StyledFormMixin, forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('full_name', 'display_name', 'email', 'school')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2:
            if p1 != p2:
                self.add_error('password2', 'Passwords do not match.')
            else:
                try:
                    validate_password(p1)
                except forms.ValidationError as e:
                    self.add_error('password1', e)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'autofocus': True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'

    def clean(self):
        email = (self.cleaned_data.get('username') or '').lower()
        password = self.cleaned_data.get('password')
        if not email or not password:
            return self.cleaned_data

        user = User.objects.filter(email__iexact=email).first()

        if user and user.locked_until and user.locked_until > timezone.now():
            mins = int((user.locked_until - timezone.now()).total_seconds() // 60) + 1
            raise forms.ValidationError(
                f'Too many failed attempts. Try again in about {mins} minute(s).', code='locked')

        self.user_cache = authenticate(self.request, username=email, password=password)

        if self.user_cache is None:
            if user and user.is_active:
                user.failed_login_count += 1
                if user.failed_login_count >= MAX_FAILED:
                    user.locked_until = timezone.now() + timedelta(minutes=LOCK_MINUTES)
                    user.failed_login_count = 0
                user.save(update_fields=['failed_login_count', 'locked_until'])
            raise self.get_invalid_login_error()

        self.confirm_login_allowed(self.user_cache)
        self.user_cache.failed_login_count = 0
        self.user_cache.locked_until = None
        self.user_cache.save(update_fields=['failed_login_count', 'locked_until'])
        return self.cleaned_data


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('full_name', 'display_name', 'school', 'profile_photo', 'show_on_leaderboard')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()