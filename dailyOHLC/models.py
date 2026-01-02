from django.db import models
class OHLCDataRCDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCDaily'
        verbose_name_plural = 'OHLCDataRCDaily'
        db_table = 'ohlc_data_rc_daily'

class OHLCDataKCDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCDaily'
        verbose_name_plural = 'OHLCDataKCDaily'
        db_table = 'ohlc_data_kc_daily'

class ImpliedVolatility(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    implied_volatility_rc = models.FloatField(null=True, blank=True)
    implied_volatility_kc = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'ImpliedVolatility'
        verbose_name_plural = 'ImpliedVolatility'
        db_table = 'implied_volatility'