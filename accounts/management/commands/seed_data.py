import datetime
from django.core.management.base import BaseCommand
from accounts.models import ActivityType, EmissionFactor


class Command(BaseCommand):
    help = 'Seeds initial Activity Types and Philippine Emission Factors'

    def handle(self, *args, **options):
        activities = [
            {
                'code': 'SACHET_AVOIDED',
                'name': 'Single-use Sachet Avoided',
                'category': ActivityType.Category.SACHET,
                'unit': ActivityType.Unit.PIECE,
                'max_quantity_per_log': 50.0,
                'max_quantity_per_day': 100.0,
                'description': 'Brought reusable containers or bought in bulk instead of single-use tingi sachets.',
                'factor': {
                    'co2_saved_per_unit_kg': 0.01500,
                    'plastic_saved_per_unit_g': 2.500,
                    'source_reference': 'GAIA Philippines Waste Assessment and Brand Audit (2019) & UNEP LCA',
                }
            },
            {
                'code': 'JEEPNEY',
                'name': 'Traditional / Modern Jeepney',
                'category': ActivityType.Category.TRANSPORT,
                'unit': ActivityType.Unit.KM,
                'max_quantity_per_log': 50.0,
                'max_quantity_per_day': 100.0,
                'description': 'Commuted by public jeepney instead of private vehicle/ride-hail.',
                'factor': {
                    'co2_saved_per_unit_kg': 0.09200,
                    'plastic_saved_per_unit_g': 0.0,
                    'source_reference': 'DOTr Clean Air Asia Philippine Transport Emissions Baseline (2022)',
                }
            },
            {
                'code': 'TRICYCLE',
                'name': 'Public Tricycle (Shared)',
                'category': ActivityType.Category.TRANSPORT,
                'unit': ActivityType.Unit.KM,
                'max_quantity_per_log': 20.0,
                'max_quantity_per_day': 50.0,
                'description': 'Shared tricycle trip for short-distance neighborhood/campus commute.',
                'factor': {
                    'co2_saved_per_unit_kg': 0.04500,
                    'plastic_saved_per_unit_g': 0.0,
                    'source_reference': 'Clean Air Asia & UP NCTS Tricycle Emission Study',
                }
            },
            {
                'code': 'BUS',
                'name': 'City / Provincial Bus',
                'category': ActivityType.Category.TRANSPORT,
                'unit': ActivityType.Unit.KM,
                'max_quantity_per_log': 100.0,
                'max_quantity_per_day': 200.0,
                'description': 'High-capacity bus commute along major thoroughfares.',
                'factor': {
                    'co2_saved_per_unit_kg': 0.10500,
                    'plastic_saved_per_unit_g': 0.0,
                    'source_reference': 'DENR EMB National Greenhouse Gas Inventory Guidebook',
                }
            },
            {
                'code': 'LRT_MRT',
                'name': 'LRT / MRT Rapid Transit',
                'category': ActivityType.Category.TRANSPORT,
                'unit': ActivityType.Unit.KM,
                'max_quantity_per_log': 100.0,
                'max_quantity_per_day': 200.0,
                'description': 'Electric rail transit avoiding fossil-fuel street congestion.',
                'factor': {
                    'co2_saved_per_unit_kg': 0.12500,
                    'plastic_saved_per_unit_g': 0.0,
                    'source_reference': 'DOTr Metro Rail Transit Clean Energy Benchmark (2023)',
                }
            },
        ]

        today = datetime.date(2026, 1, 1)

        for item in activities:
            factor_data = item.pop('factor')
            activity, created = ActivityType.objects.update_or_create(
                code=item['code'],
                defaults=item
            )
            factor, f_created = EmissionFactor.objects.update_or_create(
                activity_type=activity,
                effective_from=today,
                defaults={
                    'co2_saved_per_unit_kg': factor_data['co2_saved_per_unit_kg'],
                    'plastic_saved_per_unit_g': factor_data['plastic_saved_per_unit_g'],
                    'source_reference': factor_data['source_reference'],
                    'effective_to': None,
                }
            )
            status_text = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f"{status_text} activity: {activity.name}"))
