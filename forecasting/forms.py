from django import forms

class DailyInputForm(forms.Form):
    date = forms.DateField(
        label="Ngày dự báo", 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    prev_close = forms.FloatField(
        label="Giá đóng cửa hôm qua (USD/Tấn)", 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    inventory = forms.FloatField(
        label="Tồn kho ICE (Bao)", 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    weather_report = forms.CharField(
        label="Báo cáo thời tiết (Copy/Paste text)", 
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'})
    )