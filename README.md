# testingCSCI490

This is a new repo that will have the same purpose as sketch-n-guess. The difference is that this repo has improvements in the game and user models. Additionally, the implementation for a custom server and websockets will be implemented in this repo. 

The 'master' branch is where the most recent code is.

Python 3.12.3
Django
virtualenv

To run:
A virtualenv is needed to run Django apps, so you must create an environment.
To install virtualenv:
```
pip install virtualenv
```
Make a new directory where you will store your environment:
```
mkdir environments
```
Inside of that directory run the following:
```
virtualenv <env_name>
```
To start the environment:
```
source <env_name>/bin/activate
```
Once the environment is set up, run the following commands from the sketch_game/sketch_game directory:
```
python3 manage.py makemigrations users
```
```
python3 manage.py migrate
```
