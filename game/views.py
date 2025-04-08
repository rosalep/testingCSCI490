from django.shortcuts import render, redirect, get_object_or_404
from .models import Game, Player, Team, TeamManager, Timer, GameManager
from users.models import CustomUser
from django.contrib import messages
from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from channels.db import database_sync_to_async
from django.contrib.auth.decorators import login_required
import random 
# Create your views here.

# group two teams together to form a game
# NOT used for players to join a team
def join_teams(request):
    if request.method == 'POST':
        return render(request, 'game/join_teams.html')

# make a new team instance
def create_team(request):
    user = request.user
    player,created = Player.objects.get_or_create(player_import=user)
    if player.player_team is not None:
        return render(request, 'game/create_team.html',  {'player': player, 'message': f'Part of a Team {player.player_team.name} already, cannot make a new team.'})
    if request.method=='POST':
        # get names
        team_name = request.POST['team_name']
        team = Team.objects.create(name=team_name, creator=player)
        # automatically add creator to team
        # handles saving and checking if a team is already assigned
        Team.objects.add_player(team, player)
        # send user to pick a team
        return render(request, 'game/open_teams.html', {'player': player}) 
    return render(request, 'game/create_team.html')

# contains the canvas, chat, and other game info
# must keep track of score, rounds, artists, time remaining, and word 
# def start_game(request, game_id):

# get list of all full teams
# randomly assigned each team to a game
# create a game and display a button to route players to their games page
def create_game(request):
    print("create_game view executed")
    # return render(request, 'game/open_teams.html', {'message': 'DEBUG MESSAGE'})

    if request.method =='POST':
        user = request.user
        player = Player.objects.get(player_import=user)

        teams = Team.objects.all()    
        # full_teams must be even for this to work
        full_teams = [team for team in teams if team.is_full == True]
        if len(full_teams) >= 2:
            team1 = random.choice(full_teams)
            full_teams.remove(team1)
            team2 = random.choice(full_teams)
            full_teams.remove(team2)
            timer = Timer.objects.create()
            game = Game.objects.create(team1=team1, team2=team2, game_timer=timer)
            # only redirect to the game details if player is part of the game
            if player.player_team == team1 or player.player_team == team2:
                print("game_detail")
                return redirect('game_detail', game_id=game.game_id)
            else:
                print("not on team")
                return render(request, 'game/open_teams.html', {'message': 'Please wait for your team to be assigned a game.'})
        else:
            print("not enmopuigh for game")
            return render(request, 'game/open_teams.html', {'message': 'Not enough teams to make a game, please wait for more players to join'})
    print("outside")
    return render(request, 'game/open_teams.html', {'message': 'whats goos'})

def game_detail(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)
    user = request.user
    # prevents game from being restarted
    if game.is_active == False:
        Game.objects.start_game(game)
    if game.game_timer.get_remaining_time==0:
        Game.objects.next_round(game)
    return render(request, 'game/game_detail.html', {'game': game,'users': user, 'remaining_time': game.game_timer.get_remaining_time()})

# show all open teams
# allows player to join a team or leave a team
def open_teams(request):
    # if request.method =='POST':
    user = request.user
    player = Player.objects.get(player_import=user)
    teams = Team.objects.all()    
    open_teams = [team for team in teams if team.is_full == False]
    return render(request, 'game/open_teams.html', {'open_teams': open_teams, 'player':player})
# logic for leaving a team
# if creator leave the team, the team is deleted
@login_required
def leave_team(request, team_id):
    team = Team.objects.get(team_id=team_id)
    if request.method == 'POST':
        try:
            player =  Player.objects.get(player_import=request.user, player_team=team)
            if team.creator==player:
                team.delete() # team needs to have a creator
            player.player_team = None
            player.save() 
            return open_teams(request)
        except Player.DoesNotExist:
            return JsonResponse({'message': 'You are not on this team.'}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'An unexpected error occurred: {str(e)}'}, status=500)
    return JsonResponse({'message': 'Invalid request'}, status=400)

@sync_to_async
def get_player(user):
    player, created = Player.objects.get_or_create(player_import=user) 
    return player

async def add_player(request, team_id):
    team = await sync_to_async(Team.objects.get)(team_id=team_id)
    if request.method == 'POST':
        # makes or creates a player 
        player = await get_player(request.user)
        try: 
            await sync_to_async(Team.objects.add_player)(team, player)
            return JsonResponse({'message': 'You have joined a team!'})
        except ValueError as e:
            return JsonResponse({'message': str(e)}, status=400)
        except ValidationError as e:
            return JsonResponse({'message': e.messages[0]}, status=400)
        except Exception as e:
            return JsonResponse({'message': f'An unexpected error occured: {str(e)}'}, status=500)
    return JsonResponse({'message': 'Invalid request'}, status=400)

def next_round(request, game_id):
    game = get_object_or_404(Game, game_id=game_id)
    Game.objects.end_round(game)
    game.game_timer = Timer.objects.create()
    Game.objects.start_round(game)
    return redirect('game_detail', game_id=game.game_id)
