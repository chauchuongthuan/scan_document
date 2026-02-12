from django.db import models
class Revenue(models.Model):
    timestamp = models.DateField(primary_key=True)
    revenue_data = models.JSONField(verbose_name="Dữ liệu doanh thu theo giờ")

    class Meta: 
        verbose_name = 'Revenue'
        verbose_name_plural = 'Revenues'
        ordering = ['timestamp']
        db_table = 'revenue'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.timestamp

class RevenueByHour(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    hour = models.IntegerField()
    total = models.FloatField(null=True, blank=True)

    class Meta: 
        verbose_name = 'RevenueByHour'
        verbose_name_plural = 'RevenueByHours'
        ordering = ['date', 'hour']
        db_table = 'revenue_by_hour'
        unique_together = ('date', 'hour')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.date