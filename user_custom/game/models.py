from django.db import models, transaction
from users.models import CustomUser
from django.utils import timezone
import datetime
import random

# Create your models here.
class Player(models.Model):
    player_id = models.AutoField(primary_key=True)
    # renamed player to player_import
    player_import = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='game_player')
    player_team = models.ForeignKey('Team', on_delete=models.CASCADE, null=True, blank=True, related_name='players') 

    def __str__(self):
        return self.player_import.username
    
class WordBank(models.Model):
    word_id = models.AutoField(primary_key=True)
    word = models.CharField(max_length=30, unique=True, default='', blank=True)

# handles team sorting logic
class TeamManager(models.Manager):
    @transaction.atomic
    def add_player(self, team, player):
        # checks if player is in team
        if player.player_team is not None:
            raise ValueError(f"Player is part of team {player.player_team} already")
        # assigns player a to the team if there is space
        if  player.objects.filter(player_team = team).count() < team.max_players:
            player.player_team = team
            player.save()
        else:
            raise ValueError(f'{team.name} is full.')

class Team(models.Model):
    team_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True)
    max_players = models.IntegerField(default=2) 
    score = models.IntegerField(null=True, default=0)
    # manager handles logic
    objects = TeamManager() 

    # checks if team has space
    @property
    def is_full(self):
        return Player.objects.filter(player_team = self).count() >= self.max_players
   

class Timer(models.Model):
    timer_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    is_running = models.BooleanField(default=False)

    def start(self, duration):
        self.start_time = timezone.now() 
        self.duration = duration
        self.end_time = self.start_time + duration
        self.is_running = True
        self.save()

    def stop(self):
        self.is_running = False
        self.save()

    def get_remaining_time(self):
        if not self.is_running or not self.end_time:
            return datetime.timedelta(0)
        remaining_time = self.end_time - timezone.now()
        if remaining_time.total_seconds() <= 0:
            self.stop()
            return datetime.timedelta(0)
        return remaining_time
    
# handles score, artist, guessing team, and word assignments
class GameManager(models.Manager):
    def assign_word(self, game):
        words = WordBank.objects.exclude(past_word=game)
        if words.exists(): 
            game.word_to_guess = random.choice(words).word
            game.past_words.add(words.first())
            game.save()
        else:
            print("There are no more words available in the word bank")

    def assign_guessers(self, game):
        game.guessers = random.choice([game.team1, game.team2])
        game.save()

    def assign_artist(self, game):
        players = Player.objects.filter(player_team=game.guessers).exclude(has_drawn=game)
        if players.exists():
            game.current_artist = random.choice(players)
            game.past_artists.add(game.current_artist)
            game.save()
        else:
            self.change_guessers(game)

    def change_guessers(self, game):
        game.guessers = game.team1 if game.guessers == game.team2 else game.team2
        game.save()

    def start_game(self, game):
        self.assign_guessers(game)
        self.assign_artist(game)
        self.assign_word(game)
        self.start_round(game)

    def end_game(self, game):
        if game.game_timer:
            game.game_timer.stop()

    def start_round(self, game):
        if game.game_timer:
            game.game_timer.start(datetime.timedelta(minutes=1))
        else:
            game.game_timer = Timer.objects.create()
            game.game_timer.start(datetime.timedelta(minutes=1))
        game.save()

    def next_round(self, game):
        if game.rounds < game.max_rounds:
            game.rounds += 1
            self.assign_artist(game)
            self.assign_word(game)
            self.start_round(game)
            game.save()

    def end_round(self, game):
        if game.game_timer:
            game.game_timer.stop()

    def update_score(self, game, team_id, points):
        if game.team1.id == team_id:
            game.team1.score += points
            game.team1.save()
        elif game.team2.id == team_id:
            game.team2.score += points
            game.team2.save()
        else:
            print(f"Team {game.game_id} not found")

class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    team1 = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='game_team1')
    team2 = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='game_team2')
    guessers = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='game_guessers')
    
    game_timer = models.OneToOneField(Timer, on_delete=models.CASCADE)
    rounds = models.IntegerField(null=True, default=0)
    max_rounds = models.IntegerField(null=True, default=4)
    max_players = models.IntegerField(null=True, default=4)

    current_artist = models.ForeignKey(Player, null=True, blank=True, on_delete=models.CASCADE, related_name='artist')
    past_artists = models.ManyToManyField(Player, related_name='has_drawn')
    word_to_guess = models.CharField(max_length=30, blank=True, null=True) 
    past_words = models.ManyToManyField(WordBank, related_name='past_word')
    objects = GameManager()

# used to create a rankings page
class Ranking(models.Model):
    team_name = models.ForeignKey(Team, on_delete=models.CASCADE)
    team_score = models.IntegerField()

    def order_scores(self):
        scores = Ranking.objects()
        if scores.exists():
            print("{scores.team_score} {scores.team_name}")
