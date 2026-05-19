from django.test import TestCase

from ml_service.views import (
    _build_openmeteo_forecast_chart_data,
    _convert_historical_to_forecast_format,
    _normalize_rainfall_amount,
)


class WeatherForecastDataTest(TestCase):
    def test_trace_rainfall_is_treated_as_zero(self):
        self.assertEqual(_normalize_rainfall_amount(0.4), 0.0)
        self.assertEqual(_normalize_rainfall_amount(0.49), 0.0)
        self.assertEqual(_normalize_rainfall_amount(0.5), 0.5)

    def test_openmeteo_forecast_chart_data_uses_actual_daily_dates_and_values(self):
        payload = {
            'daily': {
                'time': ['2026-04-25', '2026-04-26'],
                'temperature_2m_max': [31.8, 30.6],
                'temperature_2m_min': [24.2, 23.9],
                'precipitation_sum': [4.5, 10.2],
                'relative_humidity_2m_mean': [78, 84],
                'wind_speed_10m_max': [12.4, 18.1],
            },
            'hourly': {
                'time': ['2026-04-25T00:00', '2026-04-25T01:00'],
                'temperature_2m': [26.1, 25.8],
                'relative_humidity_2m': [83, 84],
                'wind_speed_10m': [8.2, 7.5],
                'precipitation': [0.0, 0.2],
            }
        }

        chart_data = _build_openmeteo_forecast_chart_data(payload, 'Rice')

        self.assertEqual(chart_data['dates'], ['2026-04-25', '2026-04-26'])
        self.assertEqual(chart_data['temperature_max'], [31.8, 30.6])
        self.assertEqual(chart_data['rainfall'], [4.5, 10.2])
        self.assertEqual(chart_data['humidity_mean'], [78.0, 84.0])
        self.assertEqual(chart_data['wind_speed_max'], [12.4, 18.1])

    def test_historical_conversion_prefers_actual_rain_sum(self):
        payload = {
            'latitude': 13.1431,
            'longitude': 123.7438,
            'daily': {
                'time': ['2026-04-20'],
                'temperature_2m_max': [32.1],
                'temperature_2m_min': [24.8],
                'precipitation_sum': [12.5],
                'rain_sum': [0.0],
                'relative_humidity_2m_mean': [81],
                'relative_humidity_2m_max': [92],
                'wind_speed_10m_max': [11.2],
            }
        }

        converted = _convert_historical_to_forecast_format(payload)

        self.assertEqual(len(converted['daily_forecast']), 1)
        self.assertEqual(converted['daily_forecast'][0]['rain_sum'], 0.0)
        self.assertEqual(converted['daily_forecast'][0]['precipitation_sum'], 12.5)
        self.assertEqual(converted['daily_forecast'][0]['humidity_mean'], 81)
