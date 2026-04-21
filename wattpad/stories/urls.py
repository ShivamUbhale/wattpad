from django.urls import path

from . import views

urlpatterns = [
    path('', views.homepage_view, name='home'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path(
        'story/<int:story_id>/chapter/<int:chapter_number>/',
        views.chapter_view,
        name='chapter_detail',
    ),
    path(
        'story/<int:story_id>/chapter/<int:chapter_number>/poll/',
        views.poll_view,
        name='poll_view',
    ),
    path(
        'story/<int:story_id>/chapter/<int:chapter_number>/results/',
        views.poll_results_view,
        name='poll_results',
    ),
]
