import sys

from django.contrib.auth.models import User
from django.test import TestCase

from gatherer.models import Log
from model_builder import user_ratings_builder
from recommender_libraries.title_popularity import generate_recommendations
from import_games import import_max_range


class RecommenderTest(TestCase):

    def setUp(self):
        user = User.objects.create(username='Test')
        id = user.id

        log_objects = ({'id': 1, 'created': '2020-01-15 00:00:00', 'event_type': 'rec_view_event',
                        'content_id': 11800, 'user_id': id},
                       {'id': 2, 'created': '2020-01-15 00:00:00', 'event_type': 'wishlist_event',
                        'content_id': 11800, 'user_id': id},
                       {'id': 3, 'created': '2020-01-15 00:00:00', 'event_type': 'detail_view_event',
                        'content_id': 11800, 'user_id': id},
                       {'id': 4, 'created': '2020-01-15 00:00:00', 'event_type': 'detail_view_event',
                        'content_id': 23331, 'user_id': id},
                       {'id': 5, 'created': '2020-01-15 00:00:00', 'event_type': 'detail_view_event',
                        'content_id': 28210, 'user_id': id},
                       {'id': 6, 'created': '2020-01-15 00:00:00', 'event_type': 'wishlist_event',
                        'content_id': 28210, 'user_id': id},
                       {'id': 7, 'created': '2020-01-15 00:00:00', 'event_type': 'purchase_event',
                        'content_id': 28210, 'user_id': id},
                       {'id': 8, 'created': '2020-01-15 00:00:00', 'event_type': 'rec_view_event',
                        'content_id': 28210, 'user_id': id},
                       {'id': 9, 'created': '2020-01-15 00:00:00', 'event_type': 'detail_view_event',
                        'content_id': 59849, 'user_id': id},
                       {'id': 10, 'created': '2020-01-15 00:00:00', 'event_type': 'rec_view_event',
                        'content_id': 6036, 'user_id': id})

        for item in log_objects:
            Log.objects.create(id=item['id'], created=item['created'], event_type=item['event_type'],
                               content_id=item['content_id'], user_id=item['user_id'])

        import_max_range(20)

    def test_user_ratings_calculated_correctly(self):
        user = User.objects.get(username='Test')
        ratings = user_ratings_builder.calculate_ratings_for_user(user.id)

        self.assertEqual(ratings['11800'], 6.0, "Rating incorrect.")  # 150
        self.assertEqual(ratings['23331'], 2.0, "Rating incorrect.")  # 50
        self.assertEqual(ratings['28210'], 10.0, "Rating incorrect.")  # 250
        self.assertEqual(ratings['59849'], 2.0, "Rating incorrect.")  # 50
        self.assertEqual(ratings['6036'], 1.0, "Rating incorrect.")  # 25

    def test_top_ten_games_fetched(self):
        n = 10
        recs = generate_recommendations(n)
        self.assertEqual('1020', recs[0]['game_id'])
        self.assertEqual(n, len(recs), "Length of recommendations list should equal number generated.")

