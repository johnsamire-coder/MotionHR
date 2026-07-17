from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from core.models import TenantModel


def attachment_upload_path(instance, filename):
    from datetime import datetime
    now = datetime.now()
    return f'attachments/{now.year}/{now.month:02d}/{filename}'


def thumbnail_upload_path(instance, filename):
    from datetime import datetime
    now = datetime.now()
    return f'thumbnails/{now.year}/{now.month:02d}/{filename}'


class Attachment(TenantModel):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('word', 'Word Document'),
        ('excel', 'Excel Spreadsheet'),
        ('other', 'Other'),
    ]

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    file = models.FileField(upload_to=attachment_upload_path)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField(help_text='Size in bytes')
    mime_type = models.CharField(max_length=100)

    thumbnail = models.ImageField(
        upload_to=thumbnail_upload_path,
        null=True,
        blank=True
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments'
    )
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'core_attachments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['company', 'created_at']),
        ]
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'

    def __str__(self):
        return f'{self.original_name} ({self.file_type})'

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def is_image(self):
        return self.file_type == 'image'
