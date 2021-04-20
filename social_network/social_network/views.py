from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.db import connection
import django.utils.timezone
from .forms import RegisterForm


def user_register(request):
    # if this is a POST request we need to process the form data
    template = 'register.html'
    User = apps.get_model('accounts', 'User')
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if User.objects.raw('Select * from accounts_user where username = %s', [form.cleaned_data['username']]):
                return render(request, template, {
                    'form': form,
                    'error_message': 'Username already exists.'
                })
            elif form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form,
                    'error_message': 'Passwords do not match.'
                })
            else:
                # Create the user:

                user = User.objects.create_user(
                     username=form.cleaned_data['username'],
                     password=form.cleaned_data['password'],
                )

                user.username = form.cleaned_data['username']
                user.password = form.cleaned_data['password']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.age = form.cleaned_data['age']
                user.city = form.cleaned_data['city']
                user.interests = form.cleaned_data['interests']

                user.save()

                # Login the user
                login(request, user)

                # redirect to accounts page:
                return HttpResponseRedirect(f'/accounts/{user.id}/')
                #return HttpResponse('Beast!!!!!')

    # No post data availabe, let's just show the page.
    else:
        form = RegisterForm()

    return render(request, template, {'form': form})


def user_login(request):
    if request.method == 'POST':
        # Process the request if posted data are available
        username = request.POST['username']
        password = request.POST['password']
        # Check username and password combination if correct
        user = authenticate(username=username, password=password)
        if user is not None:
            # Save session as cookie to login the user
            login(request, user)
            # Success, now let's login the user.
            return HttpResponseRedirect(f'/accounts/{user.id}/')

            # Incorrect credentials, let's throw an error to the screen.
        return render(request, 'login.html', {'error_message': 'Incorrect username and / or password.'})

        # No post data availabe, let's just show the page to the user.
    return render(request, 'login.html')


def user_account(request, id):
    User = apps.get_model('accounts', 'User')
    FriendRequests = apps.get_model('accounts', 'FriendRequest')

    user = User.objects.raw(f'SELECT * FROM accounts_user WHERE id = %s', [id])[0]
    allusers = User.objects.raw('SELECT * FROM accounts_user')
    all_friend_requests = FriendRequests.objects.raw(
        'SELECT * from accounts_FriendRequest WHERE to_user_id = %s', [id]
    )
    context = {'username': user.username,
               'first_name': user.first_name,
               'last_name': user.last_name,
               'age': user.age,
               'city': user.city,
               'interests': user.city,
               'friends': [friend for friend in user.friends.all()],
               "allusers": allusers,
               "all_friends_requests": all_friend_requests,
               }
    if user:
        return render(request, 'account.html', context)
    return render(request, 'login.html')


@login_required
def send_friend_request(request, userID):
    User = apps.get_model('accounts', 'User')
    FriendRequest = apps.get_model('accounts', 'FriendRequest')
    from_user = request.user
    to_user = User.objects.raw(f'SELECT * FROM accounts_user WHERE id = %s', [userID])[0]
    friend_request, created = FriendRequest.objects.get_or_create(from_user=from_user, to_user=to_user)
    if created:
        return HttpResponseRedirect(f'/accounts/{request.user.id}')
    return HttpResponse('friend request was already sent')


@login_required
def accept_friend_request(request, requestID):
    FriendRequest = apps.get_model('accounts', 'FriendRequest')
    friend_request = FriendRequest.objects.get(id=requestID)
    if friend_request.to_user == request.user:
        friend_request.to_user.friends.add(friend_request.from_user)
        friend_request.from_user.friends.add(friend_request.to_user)
        friend_request.delete()
        return HttpResponseRedirect(f'/accounts/{request.user.id}')
    return HttpResponse('friend request was not accepted')
