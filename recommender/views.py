import random
from datetime import datetime

import pytz
from django.db.models import Avg, F
from django.http import JsonResponse

from gameplan.models import Game, Genre
from gatherer.models import Log
from recommender.models import RecommendationPairing
from recommender_libraries import title_similarity, title_popularity
from model_builder.user_ratings_builder import get_rating_for_user
from accounts.views import check


def get_content_based_recommendations_json(request, game_id, n=10):
    """ Gets the n most similar titles to the given game_id
     @:returns a JSON response containing information about each similar game."""
    games = get_content_based_recommendations(request, game_id, n)
    games_return_data = {
        'original_game_id': game_id,
        'data': games
    }

    return JsonResponse(games_return_data, safe=False)


def get_content_based_recommendations(request, game_id, n=10):
    """ Gets the n most similar titles to the given game_id
     @:returns a list containing information about each similar game."""
    games = title_similarity.generate_recommendations(game_id, n)
    uid = request.user.id
    game_data = list()
    for g_id in games:
        if uid is None or not check(uid, 'dislike', g_id):
            game_data.append(list(Game.objects.filter(game_id=g_id).values())[0])

    return game_data


def get_top_charts_recommendations(request, n=10):
    """ Gets the n most popular titles currently.
     @:returns a queryset of titles. """
    return title_popularity.generate_recommendations(n)


def get_bought_together_recommendations(request, game_id, n=10):
    """ Get the n most bought together titles based on the the given game.
     @:returns a JSON response containing information about each bought together game. """
    from_game = Game.objects.get(game_id=game_id)
    recs = RecommendationPairing.objects.filter(from_game=from_game).order_by('-confidence')[:n]

    uid = request.user.id
    game_data = list()
    for rec in recs:
        to_game = rec.to_game
        if uid is None or not check(uid, 'dislike', to_game.game_id):
            game_data.append(list(Game.objects.filter(game_id=to_game.game_id).values())[0])

    games_return_data = {
        'original_game_id': game_id,
        'data': game_data
    }

    return JsonResponse(games_return_data, safe=False)


def get_users_like_you_recommendations(request, n=50):
    """ Get n number of games based on users similar to the logged-in user.
     @:returns a JSON response containing information about 'like you' game. """
    uid = request.user.id
    return JsonResponse(users_like_you(uid, n), safe=False)


def users_like_you(uid, n):
    games_return_data = None
    if uid is not None:
        events = Log.objects.filter(user_id=uid).order_by('-created').values_list('content_id', flat=True).distinct()
        newest_events = list(events[:20])

        pairings = RecommendationPairing.objects.filter(from_game_id__in=newest_events) \
            .annotate(avg_confidence=Avg('confidence')).order_by('-avg_confidence')

        game_data = list()
        confidence = list()
        for rec in pairings:
            to_game = rec.to_game
            if not check(uid, 'dislike', to_game.game_id):
                game = list(Game.objects.filter(game_id=to_game.game_id).values())[0]
                if game not in game_data:
                    confidence.append(rec.confidence)
                    game_data.append(game)

        games_return_data = {
            'user_id': uid,
            'confidence': confidence[:n],
            'data': game_data[:n]

        }

    return games_return_data


def get_similar_to_recent_recommendations(request, n=50):
    """ Get n number of games based on what the user has looked at recently
     @:returns a JSON response containing information about similar game. """
    uid = request.user.id
    games_return_data = None
    if uid is not None:
        events = Log.objects.filter(user_id=uid, event_type='detail_view_event').order_by('-created') \
            .values_list('content_id', flat=True).distinct()

        if len(events) > 0:
            newest_events = list(events[:1])

            games = get_content_based_recommendations(request, newest_events[0], n)

            based_on_title = Game.objects.get(game_id=newest_events[0]).title
            games_return_data = {
                'user_id': uid,
                'based_on_title': based_on_title,
                'data': games
            }

    return JsonResponse(games_return_data, safe=False)


def get_top_genre_recommendations(request, genre_id, n=50):
    """ Gets the most popular games for a given genre id.
     @:returns a JSON response containing information about the most popular games. """
    uid = request.user.id
    games = Game.objects.select_related().filter(genres__genre_id=genre_id).order_by('-popularity')[:n]

    game_data = list()
    for game in games:
        g_id = game.game_id
        if (uid is not None and not check(uid, 'dislike', g_id)) or uid is None:
            game_data.append(list(Game.objects.filter(game_id=g_id).values())[0])

    games_return_data = {
        'data': game_data
    }

    return JsonResponse(games_return_data, safe=False)


def get_random_recommendations(request, n=50):
    """ Gets n random titles.
         @:returns a JSON response containing information about the randomly selected games. """
    games_qs = Game.objects.order_by('?').values()[:n]

    game_data = list()
    for game in games_qs:
        game_data.append(game)

    games_return_data = {
        'data': game_data
    }

    return JsonResponse(games_return_data, safe=False)


def get_coming_soon_recommendations(request, n=50):
    """ Gets the next releases ordered by released date from today's date.
         @:returns a JSON response containing information about the upcoming games. """
    date = datetime.now(pytz.utc)
    unix_time = date.timestamp()

    games_qs = Game.objects.filter(first_release_date__gt=unix_time).order_by('first_release_date').values()[:n]

    game_data = list()
    for game in games_qs:
        game_data.append(game)

    games_return_data = {
        'data': game_data
    }

    return JsonResponse(games_return_data, safe=False)


def get_top_rated_recommendations(request, n=50):
    """ Gets the next releases ordered by released date from today's date.
         @:returns a JSON response containing information about the upcoming games. """
    games_qs = Game.objects.order_by('-total_rating').values()[:n]

    game_data = list()
    for game in games_qs:
        game_data.append(game)

    games_return_data = {
        'data': game_data
    }

    return JsonResponse(games_return_data, safe=False)


NUM_LIKED = 5  # 'Because you liked game x...'
NUM_GENRES = 5  # 'Because you like genre x...'
NUM_GENRES_GENERIC = 5  # 'Popular genre x games...'


def get_recommender_categories(request):
    """ Generates the categories of recommendations.
     @:returns """
    cats = list()
    if request.user.is_authenticated:  # show personalised recs
        game_ratings = get_rating_for_user(request.user)

        # 'Because you liked game x...'
        content_qs = game_ratings.order_by('-user_rating').select_related() \
            .values('game_id', 'game__title')[:NUM_LIKED]
        cats.extend(process_qs_to_list(content_qs, 'content_based'))

        # 'Because you like genre x...'
        genres_qs = game_ratings.order_by('-user_rating').select_related() \
            .values(genre_id=F('game__genres__genre_id'), name=F('game__genres__name')).distinct()[:NUM_GENRES]
        cats.extend(process_qs_to_list(genres_qs, 'genre_based'))

    genres_qs = Genre.objects.order_by('?').values()[:NUM_GENRES_GENERIC]
    cats.extend(process_qs_to_list(genres_qs, 'genre_based_generic'))

    random.shuffle(cats)  # Randomise the order of recommendations
    return cats


def process_qs_to_list(qs, cat):
    ls = list()
    for item in qs:
        if cat == 'genre_based' or cat == 'genre_based_generic':
            item['name'] = item['name'].lower()
        dic = dict()
        dic[cat] = item
        if dic not in ls:
            ls.append(dic)

    return ls
