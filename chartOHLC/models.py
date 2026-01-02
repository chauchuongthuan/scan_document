# models.py
from django.db import models

class OHLCDataRC(models.Model):
    symbol = models.CharField(max_length=20)
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        unique_together = ('symbol', 'timestamp') # Tránh trùng nến
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRC'
        verbose_name_plural = 'OHLCDataRC'
        db_table = 'ohlc_data_rc'

class OHLCDataKC(models.Model):
    symbol = models.CharField(max_length=20)
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        unique_together = ('symbol', 'timestamp') # Tránh trùng nến
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKC'
        verbose_name_plural = 'OHLCDataKC'
        db_table = 'ohlc_data_kc'