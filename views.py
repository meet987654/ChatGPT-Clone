from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Chat
import google.generativeai as genai


genai.configure(api_key="AIzaSyCC4IwPrhyMKPe-NRn8Nrbssf0tZ_k6Nd4")


def ask_gemini(message):
    model = genai.GenerativeModel("gemini-1.5-flash")
    refined_message = f"Provide a concise answer to: {message}"
    try:
        response = model.generate_content(refined_message)
        cleaned_response = response.text.strip() if response and hasattr(response, 'text') else "No response from Gemini."
        cleaned_response = cleaned_response.replace("*", " ")
        return cleaned_response
    except Exception as e:
        return f"Error occurred: {str(e)}"


def chatbot(request):
    if not request.user.is_authenticated:
        return redirect('login')
    chats = Chat.objects.filter(user=request.user)
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            response = ask_gemini(message)
            chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
            chat.save()
            return JsonResponse({'message': message, 'response': response})
        return JsonResponse({'error': 'No message provided'}, status=400)
    return render(request, 'chatbot.html', {'chats': chats})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            error_message = 'Passwords do not match'
            return render(request, 'register.html', {'error_message': error_message})
        if User.objects.filter(username=username).exists():
            error_message = f'Username "{username}" is already taken.'
            return render(request, 'register.html', {'error_message': error_message})
        if User.objects.filter(email=email).exists():
            error_message = f'Email "{email}" is already in use.'
            return render(request, 'register.html', {'error_message': error_message})
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            auth.login(request, user)
            return redirect('chatbot')
        except Exception as e:
            error_message = f'Error creating account: {str(e)}'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')


def logout(request):
    auth.logout(request)
    return redirect('login')
