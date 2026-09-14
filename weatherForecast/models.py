from django.db import models

class CoffeeRegionWeatherForecast(models.Model):
    id = models.AutoField(primary_key=True)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coffee_region_weather_forecast'
        unique_together = ('country', 'region')
        verbose_name = "CoffeeRegionWeatherForecast"
        verbose_name_plural = "CoffeeRegionWeatherForecasts"

    def __str__(self):
        return f"{self.country} - {self.region}"

class WeatherProblemHistory(models.Model):
    SEVERITY_CHOICES = [
        ('Đỏ', 'Đỏ'),
        ('Tệ', 'Tệ'),
        ('Vấn đề', 'Vấn đề'),
    ]

    id = models.AutoField(primary_key=True)
    coffee_region = models.ForeignKey(
        CoffeeRegionWeatherForecast, 
        on_delete=models.CASCADE, 
        related_name='problem_histories',
    )
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=150)
    date = models.DateField()
    frost_drought_index = models.FloatField()
    note = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'weather_problem_histories'
        unique_together = ('coffee_region', 'date')
        ordering = ['-date', 'country', 'region']
        verbose_name = "WeatherProblemHistory"
        verbose_name_plural = "WeatherProblemHistories"

    def __str__(self):
        return f"{self.date} | {self.country} - {self.region}: {self.note} ({self.frost_drought_index})"

class WeatherForecastHistory(models.Model):
    SEVERITY_CHOICES = [
        ('Đỏ', 'Đỏ'),
        ('Tệ', 'Tệ'),
        ('Vấn đề', 'Vấn đề'),
    ]

    id = models.AutoField(primary_key=True)
    coffee_region = models.ForeignKey(
        CoffeeRegionWeatherForecast, 
        on_delete=models.CASCADE, 
        related_name='forecast_histories',
    )
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=150)
    date = models.DateField()
    frost_drought_index = models.FloatField()
    note = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'weather_forecast_histories'
        unique_together = ('coffee_region', 'date')
        ordering = ['-date', 'country', 'region']
        verbose_name = "WeatherForecastHistory"
        verbose_name_plural = "WeatherForecastHistories"

    def __str__(self):
        return f"{self.date} | {self.country} - {self.region}: {self.note} ({self.frost_drought_index})"
