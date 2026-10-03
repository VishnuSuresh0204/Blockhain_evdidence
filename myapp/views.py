from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from .models import *

def home(request):
    return render(request,"home.html")

def user_home(request):
    return render(request,"USER/home.html")


def admin_home(request):
    return render(request,"ADMIN/home.html")


def login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Django login session
            auth_login(request, user)

            # Your custom sessions
            request.session['userid'] = user.id
            request.session['username'] = user.username
            request.session['usertype'] = user.user_type

            if user.user_type == 'Admin':
                return redirect('/admin_home')

            elif user.user_type == 'User':
                return redirect('/user_home')

            else:
                messages.error(request, 'Invalid user type')
                return redirect('/login')

        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')


def logout(request):

    auth_logout(request)
    request.session.flush()

    return redirect('/login')



def registration(request):

    if request.method == 'POST':

        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        password = request.POST.get('password')

        if Login.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('registration')

        if Login.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('registration')

        user = Login.objects.create(
            username=username,
            email=email,
            password=password,
            user_type='User',
            view_pass=password
        )

        Registration.objects.create(
            user=user,
            name=name,
            email=email,
            phone=phone,
            address=address
        )

        messages.success(request, 'Registration completed successfully')

        return redirect('login')

    return render(request, 'registration.html')