from django.urls import path

from games import views

urlpatterns = [
    path('<int:game_id>', views.GameDetails.as_view(), name='game_details'),
    path('screenshots/<int:game_id>', views.get_screenshots_by_game_id, name='screenshots')
]
