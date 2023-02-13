from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import IssueForm
from .models import Issue
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm


# show the user login from the default django login form


# show the user registration form

# save the user registration form

# show the user profile

# show the commited issues

# login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# logout the user
def logout_view(request):
    logout(request)
    return redirect('index')


# show the floating action button
def fab(request):
    return render(request, 'issuetracker/fab.html')


# show the issue form
@login_required
def issue_create(request):
    form = IssueForm()
    return render(request, 'issuetracker/issue_form.html', {'form': form})

# save the issue
@login_required
def issue_submit(request):
    if request.method == "POST":
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.user = request.user
            issue.status = 'open'
            issue.priority = 'normal'
            issue.email = request.user.email
            issue.save()

            # upload the issue to github

            # get the issue link

            return redirect('home')
    else:
        form = IssueForm()
    return render(request, 'issuetracker/issue_form.html', {'form': form})

# get the right file for the dataset
#/data/dumps/<dataset>/current/<file>.ttl

# get the row number in the turtle file for the issue in the right dataset
def find_triple_line_number(uri, file):
    with open(file, 'r') as f:
        for i, line in enumerate(f, 1):
            if uri in line:
                return i
    return None


# display the issue
# Todo: add later

# close the issue
@login_required
def issue_close(request, issue_uuid ):
    issue = Issue.objects.get(pk=issue_uuid)
    issue.status = 'closed'
    issue.save()

    # TODO: close the issue on github

    return redirect('home')
