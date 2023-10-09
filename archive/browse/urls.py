from django.urls import path

from . import views

app_name = 'browse'
urlpatterns = [
    path("", views.IndexArchiveView.as_view(), name="index"),
    path("about/", views.about, name="about"),
    path("<str:collection>/", views.CollectionView.as_view(), name="collection"),
    path("<str:collection>/<str:session>/", views.SessionView.as_view(), name="session"),
    path("<str:collection>/<str:session>/<str:filetype>", views.TextView.as_view(), name="detail"),
    path('<str:collection>/<str:session>/<str:filetype>/play', views.videoView, name='video_view'),
    path('download/<int:file_id>', views.download_file, name='download_file'),
]