# models.py
from django.db import models

class OHLCDataRC(models.Model):
    id = models.BigAutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    timestamp = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        unique_together = ('symbol', 'timestamp')
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRC'
        verbose_name_plural = 'OHLCDataRC'
        db_table = 'ohlc_data_rc'

class OHLCDataKC(models.Model):
    id = models.BigAutoField(primary_key=True)
    symbol = models.CharField(max_length=20)
    timestamp = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        unique_together = ('symbol', 'timestamp')
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKC'
        verbose_name_plural = 'OHLCDataKC'
        db_table = 'ohlc_data_kc'