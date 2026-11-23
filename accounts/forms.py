from datetime import timedelta
from decimal import Decimal
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.db.models import Sum, Q
from django.utils import timezone
from .models import User, ActivityType, EmissionFactor, HabitLog

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


class HabitLogForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = HabitLog
        fields = ('activity_type', 'quantity', 'log_date', 'notes', 'proof_image')
        widgets = {
            'log_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional details (e.g. Took 10F jeepney from Labangon to CIT-U, used refillable tumbler...)'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['activity_type'].queryset = ActivityType.objects.filter(is_active=True)
        self.fields['activity_type'].empty_label = 'Select an Eco-Habit / Commute'
        if not self.initial.get('log_date') and not (self.instance and self.instance.pk):
            self.initial['log_date'] = timezone.localdate()
        self.style_fields()

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        activity = self.cleaned_data.get('activity_type')
        if qty is not None and qty <= 0:
            raise forms.ValidationError('Quantity must be greater than zero.')
        if activity and qty is not None:
            if activity.category == ActivityType.Category.SACHET:
                if qty % 1 != 0:
                    raise forms.ValidationError('Sachet quantities must be whole numbers (pieces).')
            if qty > activity.max_quantity_per_log:
                raise forms.ValidationError(
                    f"Maximum allowed for {activity.name} per log is {activity.max_quantity_per_log} {activity.unit}."
                )
        return qty

    def clean_log_date(self):
        log_date = self.cleaned_data.get('log_date')
        if log_date:
            today = timezone.localdate()
            if log_date > today:
                raise forms.ValidationError('Log date cannot be in the future.')
            if log_date < today - timedelta(days=7):
                raise forms.ValidationError('Logs can only be recorded for dates within the last 7 days.')
        return log_date

    def clean_proof_image(self):
        image = self.cleaned_data.get('proof_image')
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Proof photo size must be 5 MB or less.')
        return image

    def clean(self):
        cleaned = super().clean()
        activity = cleaned.get('activity_type')
        qty = cleaned.get('quantity')
        log_date = cleaned.get('log_date')

        if activity and qty and log_date and self.user:
            existing_logs = HabitLog.objects.filter(
                user=self.user,
                activity_type=activity,
                log_date=log_date
            )
            if self.instance and self.instance.pk:
                existing_logs = existing_logs.exclude(pk=self.instance.pk)
            day_total = existing_logs.aggregate(total=Sum('quantity'))['total'] or Decimal('0')
            if day_total + qty > activity.max_quantity_per_day:
                remaining = max(Decimal('0'), activity.max_quantity_per_day - day_total)
                raise forms.ValidationError(
                    f"Daily limit exceeded for {activity.name}. You already logged {day_total} {activity.unit} for {log_date}. Maximum allowed per day is {activity.max_quantity_per_day} {activity.unit} (remaining allowed today: {remaining} {activity.unit})."
                )
        return cleaned

    def save(self, commit=True):
        log = super().save(commit=False)
        if self.user and not log.user_id:
            log.user = self.user

        factor = EmissionFactor.objects.filter(
            activity_type=log.activity_type,
            effective_from__lte=log.log_date
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=log.log_date)
        ).order_by('-effective_from').first()

        if not factor:
            factor = EmissionFactor.objects.filter(activity_type=log.activity_type).order_by('-effective_from').first()

        log.factor = factor
        if factor:
            log.co2_saved_kg = round(log.quantity * factor.co2_saved_per_unit_kg, 3)
            log.plastic_saved_g = round(log.quantity * factor.plastic_saved_per_unit_g, 3)
        else:
            log.co2_saved_kg = Decimal('0.000')
            log.plastic_saved_g = Decimal('0.000')

        if commit:
            log.save()
        return log
