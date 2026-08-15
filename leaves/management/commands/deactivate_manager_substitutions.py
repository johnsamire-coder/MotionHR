from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "إيقاف تفويضات المديرين المؤقتة المنتهية"

    def handle(self, *args, **options):
        from leaves.models import ManagerSubstitution

        today = timezone.localdate()

        qs = ManagerSubstitution._base_manager.filter(
            is_active=True,
            end_date__lt=today,
        )

        count = qs.count()
        qs.update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"[MotionHR] Manager substitutions deactivated: {count}"
            )
        )
