from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'companies'
    verbose_name = 'الشركات والفروع'

    def ready(self):
        """
        بيشتغل مرة واحدة لما Django يبدأ
        هنا بنحمّل الـ Signals عشان تشتغل تلقائياً
        """
        try:
            import companies.signals  # noqa: F401
        except ImportError:
            pass
