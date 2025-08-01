from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from store.models import Order

def register(request):
    if request.user.is_authenticated:
        return redirect('store:product_list')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Аккаунт успешно создан! Добро пожаловать, {user.username}!')
            return redirect('store:product_list')
        else:
            messages.error(request, 'Ошибка при создании аккаунта. Проверьте введенные данные.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('store:product_list')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, phone_number=phone_number, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('store:product_list')
            else:
                messages.error(request, 'Неверный номер телефона или пароль.')
        else:
            messages.error(request, 'Неверный номер телефона или пароль.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из аккаунта.')
    return redirect('store:product_list')

@login_required
def profile(request):
    # Получаем заказы пользователя
    orders = Order.objects.filter(user=request.user).order_by('-created')
    
    return render(request, 'accounts/profile.html', {
        'orders': orders
    })

@login_required
def order_detail(request, order_id):
    # Получаем заказ только для текущего пользователя
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Заказ не найден.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/order_detail.html', {
        'order': order
    })
