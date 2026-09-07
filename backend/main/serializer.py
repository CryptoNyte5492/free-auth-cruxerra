from rest_framework import serializers
from .models import Race, UploadedFile

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'name', 'uploaded']

from rest_framework import serializers
from .models import Race

class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = [
            "id",
            "user",
            "uploaded_file",
            "name",
            "event",
            "date",
            "distance",
            "time_sec",
            "elevation",
            "humidity",
            "surface",
            "temperature",
        ]
        read_only_fields = ["id", "user"]
