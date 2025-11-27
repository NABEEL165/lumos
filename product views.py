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



# @login_required
# def influencer_product_list(request):
#     if request.user.user_type != 'influencer':
#         return redirect('home')

#     # Get filter parameters
#     status_filter = request.GET.get('status', 'all')
#     sort_by = request.GET.get('sort', '-created_at')

#     # Get all products for this influencer
#     products = Product.objects.filter(influencer=request.user)

#     # Apply status filter
#     if status_filter == 'active':
#         # Try to filter by is_active, but catch any exceptions
#         try:
#             products = products.filter(is_active=True)
#         except:
#             pass  # If field doesn't exist, continue without filtering
#     elif status_filter == 'inactive':
#         # Try to filter by is_active, but catch any exceptions
#         try:
#             products = products.filter(is_active=False)
#         except:
#             pass  # If field doesn't exist, continue without filtering
#     elif status_filter == 'featured':
#         # Try to filter by featured, but catch any exceptions
#         try:
#             products = products.filter(featured=True)
#         except:
#             pass  # If field doesn't exist, continue without filtering

#     # Apply sorting
#     products = products.order_by(sort_by)


#     # Get top performing products (by stock sold or other metric)
#     top_products = products.filter(is_active=True).order_by('-stock')[:5]

#     # Get all categories for filter dropdown
#     categories = Category.objects.all()

#     context = {
#         'products': products,
#         'top_products': top_products,
#         'categories': categories,
#         'status_filter': status_filter,
#         'sort_by': sort_by,
#     }
#     return render(request, 'influencer_product_list.html', context)





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



@login_required
def influencer_sold_products(request):
    """
    Display sold products for an influencer.
    This view shows products that have been sold by the logged-in influencer.
    """
    # Check if the user is an influencer
    if request.user.user_type != 'influencer':
        return redirect('home')

    # Sample data for demonstration (as there's no order system implemented yet)
    sold_products = [
        # {
        #     'order_id': 'ORD001',
        #     'customer_name': 'John Doe',
        #     'product': {
        #         'name': 'Premium T-Shirt',
        #         'image': None
        #     },
        #     'date': '2025-10-15',
        #     'total': '1,299.00'
        # },
        # {
        #     'order_id': 'ORD002',
        #     'customer_name': 'Jane Smith',
        #     'product': {
        #         'name': 'Designer Jeans',
        #         'image': None
        #     },
        #     'date': '2025-10-18',
        #     'total': '2,499.00'
        # },
        # {
        #     'order_id': 'ORD003',
        #     'customer_name': 'Robert Johnson',
        #     'product': {
        #         'name': 'Running Shoes',
        #         'image': None
        #     },
        #     'date': '2025-10-20',
        #     'total': '3,999.00'
        # },
        # {
        #     'order_id': 'ORD004',
        #     'customer_name': 'Emily Davis',
        #     'product': {
        #         'name': 'Smart Watch',
        #         'image': None
        #     },
        #     'date': '2025-10-22',
        #     'total': '12,999.00'
        # },
        # {
        #     'order_id': 'ORD005',
        #     'customer_name': 'Michael Brown',
        #     'product': {
        #         'name': 'Leather Wallet',
        #         'image': None
        #     },
        #     'date': '2025-10-25',
        #     'total': '1,899.00'
        # }
    ]

    # Sample stats data
    stats = {
        # 'monthly_revenue': '1,25,000',
        # 'weekly_revenue': '28,500',
        # 'daily_revenue': '3,200'
    }

    return render(request, 'sold_product.html', {
        'sold_products': sold_products,
        'stats': stats
    })




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
