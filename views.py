from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Review, Category
from .forms import ProductForm, ReviewForm, CategoryForm
from accounts.models import CustomUser
from orders.models import WishlistItem, Order, OrderItem
from django.contrib import messages
from django.db.models import Avg, Q, Sum
from django.http import HttpResponse






@login_required
def influencer_product_list(request):
    products = Product.objects.filter(influencer=request.user)
    return render(request, 'influencer_product_list.html', {'products': products})


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.influencer = request.user
            product.save()
            return redirect('influencer_product_list')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, influencer=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('influencer_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'edit_product.html', {'form': form})


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, influencer=request.user)
    product.delete()
    return redirect('influencer_product_list')

@login_required
def influencer_products(request, influencer_id):
    influencer = get_object_or_404(CustomUser, id=influencer_id, user_type='influencer')
    products = Product.objects.filter(influencer=influencer)

    products_with_ratings = []
    for product in products:
        avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
        avg_rating = avg_rating if avg_rating else 0
        products_with_ratings.append({
            'product': product,
            'avg_rating': avg_rating
        })

    wishlist_products = []
    if request.user.is_authenticated:
        wishlist_products = WishlistItem.objects.filter(user=request.user).values_list('product_id', flat=True)

    return render(request, 'influencer_products.html', {
        'influencer': influencer,
        'products': products,
        'products_with_ratings': products_with_ratings,
        'wishlist_products': wishlist_products
    })

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)

    return render(request, 'product_detail.html', {
        'product': product,
        'reviews': reviews
    })


from django.db.models import Prefetch

@login_required
def influencer_sold_products(request):
    user = request.user

    sold_items = OrderItem.objects.filter(
        product__influencer=user,
        order__status=Order.COMPLETED
    ).select_related('product', 'order')

    sold_products = []
    for item in sold_items:
        sold_products.append({
            'product': item.product,
            'quantity': item.quantity,
            'price': item.price,
            'total': item.price * item.quantity
        })

    return render(request, 'sold_product.html', {'sold_products': sold_products})




@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if the user already reviewed the product (optional)
    existing_review = Review.objects.filter(product=product, user=request.user).first()

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been submitted successfully!')
            return redirect('product_detail', product_id=product.id)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ReviewForm(instance=existing_review)

    return render(request, 'add_review.html', {
        'form': form,
        'product': product,
        'existing_review': existing_review
    })

@login_required
def top_products_by_influencer(request):
    # Aggregate total sales and revenue for each product
    top_products = Product.objects.annotate(
        total_sales=Sum('orderitem__quantity'),  # Sum of quantities sold
        total_revenue=Sum('orderitem__quantity') * Sum('price')  # Total revenue from the product
    ).filter(total_sales__isnull=False).order_by('-total_sales')  # Order by total sales in descending order

    # Pass the aggregated product data to the template
    return render(request, 'top_products.html', {'top_products': top_products})




def product_lists(request):
    # Get category name from the URL, default is 'All'
    category_name = request.GET.get('category', 'All')

    # Get all categories to display as buttons
    categories = Category.objects.all()

    if category_name != 'All':
        # Case-insensitive lookup for the category
        category = get_object_or_404(Category, name__iexact=category_name)
        products = Product.objects.filter(category=category)
    else:
        products = Product.objects.all()

    return render(request, 'product_list.html', {
        'categories': categories,
        'products': products,
        'selected_category': category_name
    })






def add_category(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponse('success')
    return render(request, 'add_category.html', {'form': form})
