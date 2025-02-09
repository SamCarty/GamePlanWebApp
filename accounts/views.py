import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic

from gameplan.models import Game, Platform
from accounts.models import Wishlist as WishlistModel, Dislike as DislikeModel


class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


@method_decorator(login_required, name='dispatch')
class Wishlist(generic.ListView):
    model = Game
    template_name = 'accounts/wishlist.html'

    def get_queryset(self):
        user = self.request.user
        user_id = user.id

        game_ids = WishlistModel.objects.filter(user_id=user_id).values('game_id')

        games = Game.objects.filter(game_id__in=game_ids)

        for game in games:
            frd = int(game.first_release_date)
            game.first_release_date = datetime.utcfromtimestamp(frd).strftime('%d/%m/%Y')

            game.platforms_human = list(Platform.objects.filter(
                platform_id__in=game.platforms.all().values_list('platform_id', flat=True)).values('name'))

        return games


def find_model(attribute):
    switch = {
        'wishlist': WishlistModel,
        'dislike': DislikeModel
    }

    return switch.get(attribute)


@login_required
def check_attribute(request, attribute, game_id):
    user = request.user
    user_id = user.id
    return check(user_id, attribute, game_id)


def check(user_id, attribute, game_id):
    model = find_model(attribute)

    if model.objects.filter(user_id=user_id, game_id=game_id).values('game_id').exists():
        return True
    else:
        return False


def add_remove_attribute(request):
    if request.user.is_authenticated:
        response_data = {'auth': True}

        attribute = request.POST.get('attribute')
        model = find_model(attribute)

        if model is not None:
            game_id = request.POST.get('game_id')
            user = request.user
            user_id = user.id
            game_ids = list(model.objects.filter(user_id=user_id, game_id=game_id).values('game_id'))

            if game_ids:
                # remove it
                model.objects.filter(user_id=request.user.id, game_id=game_id).delete()
                response_data['is_' + attribute] = False
            else:
                # add it
                model.objects.create(user_id=request.user.id, game_id=game_id)
                response_data['is_' + attribute] = True

        return JsonResponse(response_data, safe=False)
    else:
        json.dumps({'auth': False})
        return JsonResponse(json.dumps({'auth': False}), safe=False)
