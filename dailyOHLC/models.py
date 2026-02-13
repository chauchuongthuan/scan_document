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

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

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

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCDaily'
        verbose_name_plural = 'OHLCDataKCDaily'
        db_table = 'ohlc_data_kc_daily'

class OHLCDataKCKDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCKDaily'
        verbose_name_plural = 'OHLCDataKCKDaily'
        db_table = 'ohlc_data_kck_daily'

class OHLCDataRCKDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCKDaily'
        verbose_name_plural = 'OHLCDataRCKDaily'
        db_table = 'ohlc_data_rck_daily'

class OHLCDataKCUDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataKCUDaily'
        verbose_name_plural = 'OHLCDataKCUDaily'
        db_table = 'ohlc_data_kcu_daily'

class OHLCDataRCUDaily(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    
    volatility_open = models.FloatField(null=True, blank=True)
    volatility_close = models.FloatField(null=True, blank=True)
    volatility_high = models.FloatField(null=True, blank=True)
    volatility_low = models.FloatField(null=True, blank=True)

    stdev_vol_open_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_high_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_low_20_days = models.FloatField(null=True, blank=True)
    stdev_vol_close_20_days = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'OHLCDataRCUDaily'
        verbose_name_plural = 'OHLCDataRCUDaily'
        db_table = 'ohlc_data_rcu_daily'

class ImpliedVolatility(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    implied_volatility_rc = models.FloatField(null=True, blank=True)
    implied_volatility_kc = models.FloatField(null=True, blank=True)

    implied_volatility_kck = models.FloatField(null=True, blank=True)
    implied_volatility_rck = models.FloatField(null=True, blank=True)

    implied_volatility_kcu = models.FloatField(null=True, blank=True)
    implied_volatility_rcu = models.FloatField(null=True, blank=True)

    realized_volatility_rc_has_passed = models.BooleanField(default=False)
    realized_volatility_kc_has_passed = models.BooleanField(default=False)
    
    realized_volatility_kck_has_passed = models.BooleanField(default=False)
    realized_volatility_rck_has_passed = models.BooleanField(default=False)
    
    realized_volatility_kcu_has_passed = models.BooleanField(default=False)
    realized_volatility_rcu_has_passed = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'ImpliedVolatility'
        verbose_name_plural = 'ImpliedVolatility'
        db_table = 'implied_volatility'