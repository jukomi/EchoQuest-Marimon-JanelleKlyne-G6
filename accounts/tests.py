import datetime
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import User, ActivityType, EmissionFactor, HabitLog


class QuestLoggerTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='student@cit.edu',
            password='password123',
            full_name='Maria Santos',
            display_name='MariaS',
            school='CIT-U'
        )
        self.other_student = User.objects.create_user(
            email='other@cit.edu',
            password='password123',
            full_name='Juan Luna',
            display_name='JuanL',
            school='CIT-U'
        )
        self.sachet_activity = ActivityType.objects.create(
            code='SACHET_AVOIDED',
            name='Single-use Sachet Avoided',
            category=ActivityType.Category.SACHET,
            unit=ActivityType.Unit.PIECE,
            max_quantity_per_log=Decimal('50.00'),
            max_quantity_per_day=Decimal('100.00'),
        )
        self.factor = EmissionFactor.objects.create(
            activity_type=self.sachet_activity,
            co2_saved_per_unit_kg=Decimal('0.01500'),
            plastic_saved_per_unit_g=Decimal('2.500'),
            source_reference='GAIA 2019',
            effective_from=datetime.date(2026, 1, 1),
        )

    def test_log_creation_and_impact_calculation(self):
        self.client.login(username='student@cit.edu', password='password123')
        today = timezone.localdate()
        response = self.client.post(reverse('log_create'), {
            'activity_type': self.sachet_activity.pk,
            'quantity': '10',
            'log_date': today.isoformat(),
            'notes': 'Used my refillable coffee mug',
        })
        self.assertEqual(response.status_code, 302)
        log = HabitLog.objects.get(user=self.student)
        self.assertEqual(log.quantity, Decimal('10'))
        self.assertEqual(log.plastic_saved_g, Decimal('25.000')) # 10 * 2.5
        self.assertEqual(log.co2_saved_kg, Decimal('0.150'))    # 10 * 0.015

    def test_sachet_decimal_validation_error(self):
        self.client.login(username='student@cit.edu', password='password123')
        today = timezone.localdate()
        response = self.client.post(reverse('log_create'), {
            'activity_type': self.sachet_activity.pk,
            'quantity': '5.5',
            'log_date': today.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'quantity', 'Sachet quantities must be whole numbers (pieces).')

    def test_log_update_and_delete(self):
        self.client.login(username='student@cit.edu', password='password123')
        today = timezone.localdate()
        log = HabitLog.objects.create(
            user=self.student,
            activity_type=self.sachet_activity,
            factor=self.factor,
            quantity=Decimal('4'),
            log_date=today,
            plastic_saved_g=Decimal('10.000'),
            co2_saved_kg=Decimal('0.060'),
        )
        # Edit
        response = self.client.post(reverse('log_update', args=[log.pk]), {
            'activity_type': self.sachet_activity.pk,
            'quantity': '8',
            'log_date': today.isoformat(),
            'notes': 'Updated notes',
        })
        self.assertEqual(response.status_code, 302)
        log.refresh_from_db()
        self.assertEqual(log.quantity, Decimal('8'))
        self.assertEqual(log.plastic_saved_g, Decimal('20.000'))

        # Delete
        del_response = self.client.post(reverse('log_delete', args=[log.pk]))
        self.assertEqual(del_response.status_code, 302)
        self.assertFalse(HabitLog.objects.filter(pk=log.pk).exists())

    def test_cannot_edit_other_user_log(self):
        today = timezone.localdate()
        log = HabitLog.objects.create(
            user=self.other_student,
            activity_type=self.sachet_activity,
            factor=self.factor,
            quantity=Decimal('4'),
            log_date=today,
        )
        self.client.login(username='student@cit.edu', password='password123')
        response = self.client.post(reverse('log_update', args=[log.pk]), {
            'activity_type': self.sachet_activity.pk,
            'quantity': '10',
            'log_date': today.isoformat(),
        })
        self.assertEqual(response.status_code, 302)
        log.refresh_from_db()
        self.assertEqual(log.quantity, Decimal('4')) # unchanged
