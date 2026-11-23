from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=email.lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('role', 'ADMIN')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        ADMIN = 'ADMIN', 'Administrator'

    full_name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=255, unique=True)
    school = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    show_on_leaderboard = models.BooleanField(default=True)
    failed_login_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'display_name', 'school']

    objects = UserManager()

    def __str__(self):
        return self.display_name


class ActivityType(models.Model):
    class Category(models.TextChoices):
        SACHET = 'SACHET', 'Sachet Plastic'
        TRANSPORT = 'TRANSPORT', 'Public Transport'

    class Unit(models.TextChoices):
        PIECE = 'PIECE', 'Piece'
        KM = 'KM', 'Kilometre'

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=60)
    category = models.CharField(max_length=20, choices=Category.choices)
    unit = models.CharField(max_length=10, choices=Unit.choices)
    max_quantity_per_log = models.DecimalField(max_digits=7, decimal_places=2, default=50.00)
    max_quantity_per_day = models.DecimalField(max_digits=7, decimal_places=2, default=100.00)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"


class EmissionFactor(models.Model):
    activity_type = models.ForeignKey(ActivityType, on_delete=models.PROTECT, related_name='emission_factors')
    co2_saved_per_unit_kg = models.DecimalField(max_digits=10, decimal_places=5, default=0.0)
    plastic_saved_per_unit_g = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    source_reference = models.CharField(max_length=255)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.activity_type.name} Factor (From {self.effective_from})"


class HabitLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habit_logs')
    activity_type = models.ForeignKey(ActivityType, on_delete=models.PROTECT, related_name='logs')
    factor = models.ForeignKey(EmissionFactor, on_delete=models.PROTECT, related_name='logs')
    quantity = models.DecimalField(max_digits=7, decimal_places=2)
    log_date = models.DateField()
    notes = models.CharField(max_length=255, blank=True, null=True)
    proof_image = models.ImageField(upload_to='proofs/', blank=True, null=True)
    co2_saved_kg = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    plastic_saved_g = models.DecimalField(max_digits=10, decimal_places=3, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-log_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'log_date', 'activity_type']),
        ]

    def __str__(self):
        return f"{self.user.display_name} - {self.activity_type.name} ({self.quantity} {self.activity_type.unit}) on {self.log_date}"
