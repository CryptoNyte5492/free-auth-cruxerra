from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    # Desktop installs are commonly used without outbound email configured.
    # Let coaches sign in with the address they provided instead of a generated
    # username that would otherwise have to be emailed to them.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/')
    name = models.CharField(max_length=50)
    uploaded = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

class Race(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files", null=True, blank=True)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    event = models.CharField(max_length=100)
    date = models.CharField(max_length=20)
    distance = models.IntegerField()
    time_sec = models.FloatField()
    elevation = models.IntegerField()
    humidity = models.IntegerField()
    surface = models.CharField(max_length=15)
    temperature = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.event}"
