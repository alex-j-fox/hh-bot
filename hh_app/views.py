from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
import subprocess


def index(request):
    return render(request, 'index.html')


class LoginUserView(SuccessMessageMixin, LoginView):
    template_name = 'login.html'
    success_message = 'Вы успешно вошли в систему'
    success_url = '/'


class LogoutUserView(LogoutView):

    def post(self, request, *args, **kwargs):
        """
        Выход пользователя из системы.

        Выполняет выход пользователя из системы.
        Выводит сообщение об успешном выходе и перенаправляет на главную.
        """
        logout(request)
        messages.info(request, 'Вы вышли из системы')
        return redirect('index')


class RunBotView(TemplateView):
    template_name = 'run_bot.html'

    def post(self, request, *args, **kwargs):
        """
        Выход пользователя из системы.

        Выполняет выход пользователя из системы.
        Выводит сообщение об успешном выходе и перенаправляет на главную.
        """
        if request.user.is_authenticated:
            subprocess.Popen(['python', 'bot.py'])
            messages.info(request, 'Бот успешно запущен')
            return redirect('index')
        messages.info(request, 'Вы не вошли в систему')
        return redirect('login')


def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    return render(request, 'errors/500.html', status=500)
