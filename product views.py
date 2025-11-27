from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Review, Category
from .forms import ProductForm, ReviewForm, CategoryForm
from account.models import CustomUser, Order, OrderItem
# from orders.models import WishlistItem, Order, OrderItem  # Commented out - orders app not available
from django.contrib import messages
from django.db.models import Avg, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta






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

    # Removed wishlist functionality as it's not available in the current setup
    wishlist_products = []

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
    Display sold products for an influencer with filtering capabilities.
    Shows Order ID, customer name, product, date, amount (₹)
    With filters for month or product
    And monthly/weekly/daily revenue stats
    """
    # Check if the user is an influencer
    if request.user.user_type != 'influencer':
        return redirect('home')

    # Get filter parameters
    filter_type = request.GET.get('filter_type', '')
    filter_value = request.GET.get('filter_value', '')
    
    # Start with all order items for this influencer's products
    sold_items = OrderItem.objects.filter(
        product__influencer=request.user
    ).select_related('order', 'product', 'order__customer')
    
    # Apply filters
    if filter_type == 'month' and filter_value:
        try:
            # Parse month/year from filter_value (format: MM-YYYY)
            month, year = map(int, filter_value.split('-'))
            sold_items = sold_items.filter(
                order__created_at__year=year,
                order__created_at__month=month
            )
        except ValueError:
            pass  # Invalid format, ignore filter
    elif filter_type == 'product' and filter_value:
        try:
            product_id = int(filter_value)
            sold_items = sold_items.filter(product_id=product_id)
        except ValueError:
            pass  # Invalid product ID, ignore filter
    
    # Calculate revenue statistics
    # Monthly revenue (current month)
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = sold_items.filter(
        order__created_at__gte=start_of_month
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Weekly revenue (last 7 days)
    week_ago = today - timedelta(days=7)
    weekly_revenue = sold_items.filter(
        order__created_at__gte=week_ago
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Daily revenue (today)
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_revenue = sold_items.filter(
        order__created_at__gte=start_of_day
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Format revenue values
    stats = {
        'monthly_revenue': "{:,.2f}".format(monthly_revenue),
        'weekly_revenue': "{:,.2f}".format(weekly_revenue),
        'daily_revenue': "{:,.2f}".format(daily_revenue)
    }
    
    # Prepare sold products data for display
    sold_products = []
    for item in sold_items:
        sold_products.append({
            'order_id': item.order.id,
            'customer_name': item.order.customer.full_name or item.order.customer.username,
            'product': item.product,
            'date': item.order.created_at.strftime('%Y-%m-%d'),
            'total': "{:,.2f}".format(float(item.price))
        })
    
    # Get all products for this influencer for the filter dropdown
    influencer_products = Product.objects.filter(influencer=request.user)
    
    return render(request, 'sold_product.html', {
        'sold_products': sold_products,
        'stats': stats,
        'influencer_products': influencer_products,
        'filter_type': filter_type,
        'filter_value': filter_value
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
