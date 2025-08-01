from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Category, Product, Order, OrderItem
import json

# Create your views here.

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    return render(request, 'store/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    categories = Category.objects.all()
    return render(request, 'store/product_detail.html', {
        'product': product,
        'categories': categories
    })

def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id, available=True)
        
        cart = request.session.get('cart', {})
        if product_id in cart:
            cart[product_id]['quantity'] += quantity
        else:
            cart[product_id] = {
                'name': product.name,
                'price': str(product.price),
                'quantity': quantity
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} добавлен в корзину',
            'cart_count': sum(item['quantity'] for item in cart.values())
        })
    
    return JsonResponse({'success': False, 'message': 'Неверный запрос'})

def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    categories = Category.objects.all()
    
    for product_id, item in cart.items():
        product = Product.objects.get(id=product_id)
        item_total = product.price * item['quantity']
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'total': item_total
        })
        total += item_total
    
    return render(request, 'store/cart_detail.html', {
        'cart_items': cart_items,
        'total': total,
        'categories': categories
    })

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Товар удален из корзины')
    
    return redirect('store:cart_detail')

def order_create(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('store:product_list')
    
    if request.method == 'POST':
        # Создаем заказ
        order_data = {
            'address': request.POST['address'],
            'total_amount': 0
        }
        
        # Если пользователь авторизован, связываем заказ с ним
        if request.user.is_authenticated:
            order_data['user'] = request.user
        else:
            # Для гостевых заказов заполняем данные клиента
            order_data['customer_name'] = request.POST['customer_name']
            order_data['customer_email'] = request.POST['customer_email']
            order_data['customer_phone'] = request.POST['customer_phone']
        
        order = Order.objects.create(**order_data)
        
        total_amount = 0
        
        # Создаем позиции заказа
        for product_id, item in cart.items():
            product = Product.objects.get(id=product_id)
            price = product.price
            quantity = item['quantity']
            item_total = price * quantity
            
            OrderItem.objects.create(
                order=order,
                product=product,
                price=price,
                quantity=quantity
            )
            
            total_amount += item_total
        
        # Обновляем общую сумму заказа
        order.total_amount = total_amount
        order.save()
        
        # Очищаем корзину
        request.session['cart'] = {}
        request.session.modified = True
        
        # Для гостевых заказов сохраняем информацию в сессии
        if not request.user.is_authenticated:
            guest_order_key = f'guest_order_{order.id}'
            request.session[guest_order_key] = True
            request.session.modified = True
        
        messages.success(request, f'Заказ #{order.id} успешно создан!')
        return redirect('store:order_success', order_id=order.id)
    
    cart_items = []
    total = 0
    categories = Category.objects.all()
    
    for product_id, item in cart.items():
        product = Product.objects.get(id=product_id)
        item_total = product.price * item['quantity']
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'total': item_total
        })
        total += item_total
    
    return render(request, 'store/order_create.html', {
        'cart_items': cart_items,
        'total': total,
        'categories': categories
    })

def order_success(request, order_id):
    # Получаем заказ с проверкой прав доступа
    try:
        if request.user.is_authenticated:
            # Для авторизованных пользователей - только их заказы
            order = get_object_or_404(Order, id=order_id, user=request.user)
        else:
            # Для гостевых заказов - проверяем через сессию
            # Создаем временный ключ для гостевых заказов
            guest_order_key = f'guest_order_{order_id}'
            if guest_order_key not in request.session:
                messages.error(request, 'Доступ к заказу запрещен.')
                return redirect('store:product_list')
            
            order = get_object_or_404(Order, id=order_id)
            # Проверяем, что это действительно гостевой заказ (без пользователя)
            if order.user is not None:
                messages.error(request, 'Доступ к заказу запрещен.')
                return redirect('store:product_list')
    except:
        messages.error(request, 'Заказ не найден.')
        return redirect('store:product_list')
    
    categories = Category.objects.all()
    return render(request, 'store/order_success.html', {
        'order': order,
        'categories': categories
    })
