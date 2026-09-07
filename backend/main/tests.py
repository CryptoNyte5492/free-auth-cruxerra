from django.test import TestCase
from types import SimpleNamespace

from .math import (
    fit_athlete_performance_model,
    normalize_time,
    predict_time,
)
from .models import User


class PredictionMathTests(TestCase):
    def setUp(self):
        # Times follow the Riegel distance relationship.  The small, controlled
        # fixture makes a regression in distance scaling easy to spot.
        self.races = [
            SimpleNamespace(name="A", distance=1600, time_sec=300.0, temperature=60,
                            humidity=60, elevation=0, surface="track", date="1/1/2024"),
            SimpleNamespace(name="A", distance=3200, time_sec=300.0 * 2**1.06, temperature=60,
                            humidity=60, elevation=0, surface="track", date="2/1/2024"),
            SimpleNamespace(name="A", distance=5000, time_sec=300.0 * (5000 / 1600)**1.06,
                            temperature=60, humidity=60, elevation=0, surface="track", date="3/1/2024"),
        ]
        self.model = fit_athlete_performance_model(self.races, "A")

    def test_distance_projection_uses_stable_riegel_scaling(self):
        prediction = predict_time(self.model, 10000, 60, 60, 0, "track")
        expected = 300.0 * (10000 / 1600)**1.06
        self.assertAlmostEqual(prediction, expected, delta=1.0)

    def test_conditions_make_prediction_slower_and_normalization_is_inverse(self):
        ideal = predict_time(self.model, 5000, 60, 60, 0, "track")
        hot_grass = predict_time(self.model, 5000, 80, 75, 100, "grass")
        self.assertGreater(hot_grass, ideal)
        self.assertAlmostEqual(
            normalize_time(self.model, hot_grass, 80, 75, 100, "grass"),
            ideal,
            places=6,
        )


class LocalDesktopApiTests(TestCase):
    def test_saved_files_api_needs_no_login_and_creates_local_profile(self):
        response = self.client.get("/api/dashboard/files/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.assertTrue(User.objects.filter(username="local-coach").exists())
