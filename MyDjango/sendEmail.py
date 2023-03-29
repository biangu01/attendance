from django.shortcuts import render

def send(request):
    return render(request, 'https://mail.google.com/mail/u/0/?fs=1&tf=cm', {"test":1})