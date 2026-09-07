from .models import *
import csv, io
from .math import *
from rest_framework import status
from .serializer import RaceSerializer, FileSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

LOCAL_USERNAME = "local-coach"
LOCAL_EMAIL = "local-coach@cruxerra.local"


def get_local_user():
    """Return the single, invisible profile used by this offline desktop app."""
    user, created = User.objects.get_or_create(
        username=LOCAL_USERNAME,
        defaults={"email": LOCAL_EMAIL},
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user

class UploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        all_races = []
        uploaded_file_ids = []
        files = request.FILES.getlist("file")

        if not files:
            return Response({"error": "No files uploaded"}, status=400)

        user = get_local_user()

        try:
            for f in files:
                stream = io.StringIO(f.read().decode("utf-8"))
                f.seek(0)
                reader = csv.DictReader(stream)

                file_name = f.name
                filtered_file = UploadedFile.objects.filter(user=user, name=file_name)

                if not filtered_file.exists():
                    u_file = UploadedFile.objects.create(
                        user=user,
                        file=f,
                        name=file_name
                    )
                else:
                    u_file = filtered_file.first()

                uploaded_file_ids.append(u_file.id)

                for row in reader:
                    cleaned = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

                    exists = Race.objects.filter(
                        user=user,
                        uploaded_file=u_file,
                        name=cleaned['Athlete'],
                        event=cleaned['Event'],
                        date=cleaned['Date'],
                        distance=int(cleaned['Distance (m)']),
                    ).exists()

                    if not exists:
                        all_races.append(
                            Race(
                                user=user,
                                uploaded_file=u_file,
                                name=cleaned.get('Athlete', '').strip(),
                                event=cleaned.get('Event', '').strip(),
                                date=cleaned.get('Date'),
                                distance=safe_int(cleaned.get('Distance (m)')),
                                time_sec=parse_time_to_seconds(cleaned.get('Time', '0:00')),
                                elevation=safe_int(cleaned.get('Elevation Gain')),
                                humidity=safe_int(cleaned.get('Humidity (%)')),
                                surface=cleaned.get('Surface', '').strip(),
                                temperature=safe_int(cleaned.get('Temperature (F)')),
                            )
                        )

            if all_races:
                Race.objects.bulk_create(all_races)

            return Response({
                "message": "Upload successful",
                "file_id": uploaded_file_ids
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class UploadedFileListView(APIView):
    def get(self, request):
        files = UploadedFile.objects.filter(user=get_local_user()).order_by("-uploaded")
        return Response(FileSerializer(files, many=True).data)

class RunnerView(ModelViewSet):
    serializer_class = RaceSerializer

    def get_queryset(self):
        queryset = Race.objects.filter(user=get_local_user())

        file_id = self.request.query_params.get('file_id')
        athlete = self.request.query_params.get('athlete')

        if file_id:
            queryset = queryset.filter(uploaded_file=file_id)
        if athlete:
            queryset = queryset.filter(name=athlete)
        return queryset.order_by("name", "date")

    def perform_create(self, serializer):
        return serializer.save(user=get_local_user())

class RunnerPredictionView(APIView):
    def get(self, request):
        file_id = request.query_params.get("file_id")
        athlete = request.query_params.get("athlete")
        race_id = request.query_params.get("race_id")

        # -------------------------
        # Validate parameters
        # -------------------------
        if not race_id:
            return Response(
                {"error": "Missing race_id"},
                status=400
            )

        if not athlete:
            return Response(
                {"error": "Missing athlete"},
                status=400
            )

        # -------------------------
        # Find the selected race
        # -------------------------
        user = get_local_user()
        races = Race.objects.filter(user=user)

        if file_id:
            races = races.filter(uploaded_file=file_id)

        race = get_object_or_404(
            races,
            id=race_id
        )

        # -------------------------
        # Get conditions from race
        # -------------------------
        distance = race.distance
        elevation = race.elevation
        humidity = race.humidity
        surface = race.surface
        temp = race.temperature

        target_distance = safe_int(distance, None)
        file_races = []

        all_files = UploadedFile.objects.filter(
            user=user
        )

        for file in all_files:
            races_in_file = Race.objects.filter(
                user=user,
                uploaded_file=file
            )

            file_races.extend(races_in_file)
        target_date = to_date_safe(race.date)

        training_races = [
            candidate
            for candidate in file_races
            if (
                candidate.id != race.id
                and (
                    target_date is None
                    or (
                        to_date_safe(candidate.date) is not None
                        and to_date_safe(candidate.date) < target_date
                    )
                )
            )
        ]

        try:
            model = fit_athlete_performance_model(
                training_races,
                athlete
            )

            if model is None:
                return Response(
                    {
                        "error": "Unable to build prediction model for this athlete."
                    },
                    status=400
                )

            # Prediction under the selected race's conditions
            pred = predict_time(
                model,
                target_distance,
                temp,
                humidity,
                elevation,
                surface
            )

            # Prediction under ideal conditions
            ideal_time = ideal_time_for_distance(
                model,
                target_distance
            )

            # How much the athlete's performances vary
            std_dev = model_residual_std(
                model,
                training_races,
                athlete
            )

            # Progression history at this distance
            history = athlete_progress_history(
                model,
                training_races,
                athlete,
                target_distance
            )

        except Exception as e:
            import traceback
            traceback.print_exc()

            return Response(
                {"error": str(e)},
                status=500
            )
        if pred is None:
            return Response(
                {"error": "Not enough race data to predict"},
                status=404
            )
        return Response({
            "conditions": {
                "temp": temp,
                "humidity": humidity,
                "surface": surface,
                "elevation": elevation,
            },
            "prediction": pred,
            "ideal_time": ideal_time,
            "std_dev": std_dev,
            "history": history,
            "file_races": RaceSerializer(
                file_races,
                many=True
            ).data
        })
