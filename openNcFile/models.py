from django.db import models
from uuid import uuid4

class RainPrecip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    date = models.DateField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    precip = models.FloatField(null=True, blank=True)
    province = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'RainPrecip'
        verbose_name_plural = 'RainPrecips'
        db_table = 'rain_precip'  # tên bảng trùng với DB
        unique_together = ('date', 'latitude', 'longitude')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.id