from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.contrib.auth.decorators import login_required 
from .models import CustomUser, hash_password
from game.models import Player
from django.core.exceptions import ValidationError
from django.db import IntegrityError

# Create your views here.
def login_page(request):
    if request.method=="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user-home') #redirect after login
        else:
            return render(request, 'users/login.html', {'form': {'errors': True}})
    return render(request, 'users/login.html')

def home(request):

    # had problem earlier; remove if page breaks
    # if Player.objects.filter(player_import=request.user):
    #     curr_player = Player.objects.get(player_import=request.user)

    players = Player.objects.all().order_by('-alltime_score').values('player_import__username', 'alltime_score')
    player = [p for p in players]
    return render(request, 'users/home.html', {'player': player,})
    #  'curr_player': curr_player})

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            return render(request, 'users/signup.html', {'form': {'errors': 'Passwords do not match.'}})

        try:
            validate_email(email)  # Validate email format
            validate_password(password) 
            # Use the CustomUserManager to create the user
            user = CustomUser.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            # automatically crete a PLayer when CustomUser created        
            Player.objects.create(player_import=user)
            return redirect('user-profile')
        except ValidationError as e:
            return render(request, 'users/signup.html', {'form': {'errors': str(e)}})

        except IntegrityError:
            return render(request, 'users/signup.html', {'form': {'errors': 'Username or email already exists.'}})
        except Exception as e:
            return render(request, 'users/signup.html', {'form': {'errors': str(e)}})

    return render(request, 'users/signup.html')

def logout_view(request):
    messages.success(request, "You have been successfully logged out.")
    logout(request)
    return redirect('/')  
@login_required
def profile(request):
    player,created = Player.objects.get_or_create(player_import=request.user)
    return render(request, 'users/profile.html', {'player': player})

@login_required
def profileUpdate(request):
    # get user
    user = request.user
    player,created = Player.objects.get_or_create(player_import=user)
    if request.method == 'POST':
        if 'update_profile' in request.POST: 
            try:
                username = request.POST.get('username')
                email = request.POST.get('email')
                validate_email(email)
                avatar = request.FILES.get('avatar') # check if user submitted new avatar
                user.username = username
                user.email = email
                if avatar: # if false, keeps default avatar
                    user.avatar = avatar
                user.save()
                login(request, user)
                return redirect('user-profile')
            except ValidationError as e:
                return render(request, 'users/profileUpdate.html', {'form': {'errors': str(e)}, 'player': player})
            except IntegrityError:
                return render(request, 'users/profileUpdate.html', {'form': {'errors': 'Username or email already exists.'}, 'player': player})
            except Exception as e:
                return render(request, 'users/profileUpdate.html', {'form': {'errors': str(e)}, 'player': player})
        if 'change_password' in request.POST: 
            old_password = request.POST.get('old_password')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            if password != password2:
                    return render(request, 'users/profileUpdate.html', {'form': {'errors': 'Passwords do not match.'}, 'player': player})
            try:   
                # check old password against input
                if user.check_password(old_password):
                    validate_password(password)
                    user.password = hash_password(password)
                    user.save()
                    login(request, user)
                    return redirect('user-profile')
                else:
                    return render(request, 'users/profileUpdate.html',  {'form': {'errors': 'Old password is incorrect.'}, 'player': player})
            except ValidationError as e:
                return render(request, 'users/profileUpdate.html', {'form': {'errors': str(e)}, 'player': player})
            except Exception as e:
                return render(request, 'users/profileUpdate.html', {'form': {'errors': str(e)}, 'player': player})
        

    return render(request, 'users/profileUpdate.html', {'player': player})
