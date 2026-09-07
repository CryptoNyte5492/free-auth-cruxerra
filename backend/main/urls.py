from django.urls import path, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter();
router.register(r'runnersviews', RunnerView, basename='runners-view')

urlpatterns = [

    path("dashboard/files/", UploadedFileListView.as_view(), name="uploaded-files"),
    path('dashboard/fileUpload/', UploadView.as_view(), name='uploaded_view'),
    path('runners/prediction/', RunnerPredictionView.as_view(), name='runner_prediction'),

    path('', include(router.urls))
]
