from django.shortcuts import render, redirect, get_object_or_404
from .models import Game, Player, Team, TeamManager, Timer, GameManager
from users.models import CustomUser
from django.contrib import messages
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from channels.db import database_sync_to_async
# Create your views here.
def create_game(request):
    if request.method == 'POST':
        # get names
        team1_name = request.POST['team1_name']
        team2_name = request.POST['team2_name']
        # create teams
        team1 = Team.objects.create(name=team1_name)
        team2 = Team.objects.create(name=team2_name)
        # dont start timer yet
        timer = Timer.objects.create()
        game = Game.objects.create(team1=team1, team2=team2, game_timer=timer)
        
        # need to get all players in teams first
        Game.objects.start_game(game)
        return redirect('game_detail', game_id=game.game_id)
    return render(request, 'game/create_game.html')

def game_detail(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)
    user = request.user
    return render(request, 'game/game_detail.html', {'game': game,'users': user, 'remaining_time': game.game_timer.get_remaining_time()})

@database_sync_to_async
def get_player(user):
    player, created = Player.objects.get_or_create(player_import=user) 
    return player

async def add_player(request, team_id):
    team = get_object_or_404(Team, team_id=team_id)
    # user = get_object_or_404(CustomUser, user_id=user_id)
    if request.method == 'POST':
        # makes or creates a player 
        player = await get_player(request.user)
        try: 
            await sync_to_async(Team.objects.add_player(team, player))
            return JsonResponse({'message': 'You have joined a team!'})
        except ValueError as e:
            return JsonResponse({'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'message': e.messages[0]}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'An unexpected error occured: {str(e)}'}, status=500)

    return JsonResponse({'message': 'Invalid request'}, status=400)

    # # Check if the user is already a player
    # if Player.objects.filter(player_import=user, player_team=team).exists():
    #     messages.error(request, f"User '{user.username}' is already a player on {team.name}")
    # else:
    #     if team.is_full:
    #         messages.error(request, f"{team.name} is full")
    #     else:
    #         # Create a player with the username as player name
    #         player = Player.objects.create(player_import=user, player_team=team)
    #         messages.success(request, f"User '{user.username}' added to {team.name} as a player.")

    # users = CustomUser.objects.all() #get all users.
    # return render(request, 'game/add_player.html', {'team': team, 'users': users})

def next_round(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)
    Game.objects.end_round(game)
    game.game_timer = Timer.objects.create()
    Game.objects.start_round(game)
    return redirect('game_detail', game_id=game.game_id)

def switch_teams(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)
    Game.objects.end_round(game)
    game.game_timer = Timer.objects.create()
    Game.objects.start_round(game)
    return redirect('game_detail', game_id=game.game_id)

# displays game timer, and everything in game model
def game_page(request):
    return render(request, 'game/game.py')