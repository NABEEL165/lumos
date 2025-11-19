from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Sum, F, Q
from django.utils.timezone import now
from .forms import InfluencerRegisterForm, CustomerRegisterForm, InfluencerProfileForm
from .models import CustomUser, InfluencerProfile, InfluencerVideo
from products.models import Category, Product
from orders.models import OrderItem





def home_view(request):
    categories = Category.objects.all()
    influencers = CustomUser.objects.filter(user_type='influencer')
    products = Product.objects.all().select_related('category', 'influencer')[:12]
    context = {
        'categories': categories,
        'influencers': influencers,
        'products': products,
    }
    return render(request, 'home.html', context)




def register_influencer(request):
    if request.method == 'POST':
        form = InfluencerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                send_mail(
                    'Welcome to Influencify — Let’s Build Something Iconic!',
                    f'Hi {user.username},\n\nWelcome to Influencify! Your journey as an influencer starts here. Collaborate, create, and inspire shoppers worldwide. Let’s build something iconic!',
                    'empireaeitservices8@gmail.com',
                    [user.email],
                    fail_silently=False,
                )
            except Exception:
                pass  # Log email failure if logging is configured
            return redirect('login')
    else:
        form = InfluencerRegisterForm()
    return render(request, 'register_influencer.html', {'form': form})


def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                send_mail(
                    'Welcome to Influencify — Start Shopping!',
                    f'Hi {user.username},\n\nWelcome to Influencify! Discover unique products from top influencers and join a community of trendsetters. Start shopping now!',
                    'empireaeitservices8@gmail.com',
                    [user.email],
                    fail_silently=False,
                )
            except Exception:
                pass  # Log email failure if logging is configured
            return redirect('login')
    else:
        form = CustomerRegisterForm()
    return render(request, 'register_customer.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.user_type == 'influencer':
                return redirect('influencer_dashboard')
            return redirect('customer_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def influencer_dashboard(request):
    if request.user.user_type != 'influencer':
        return redirect('home')

    influencer = request.user

    # Handle video upload POST request
    if request.method == 'POST':
        title = request.POST.get('videoTitle')
        description = request.POST.get('videoDescription')
        video_file = request.FILES.get('videoFile')
        thumbnail = request.FILES.get('videoThumbnail')
        product_ids = request.POST.getlist('products')  # Get selected product IDs

        # Create video
        video = InfluencerVideo.objects.create(
            influencer=request.user,
            title=title,
            description=description,
            video_file=video_file,
            thumbnail=thumbnail
        )

        # Link selected products
        if product_ids:
            products = Product.objects.filter(id__in=product_ids, influencer=request.user)
            video.products.set(products)

        return redirect('influencer_dashboard')

    # Get dashboard statistics
    order_items = OrderItem.objects.filter(product__influencer=influencer).select_related('product')

    total_revenue = order_items.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
    total_orders = order_items.values('order').distinct().count()

    today = now()
    monthly_revenue = order_items.filter(
        order__created_at__year=today.year,
        order__created_at__month=today.month
    ).aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0

    monthly_orders = order_items.filter(
        order__created_at__year=today.year,
        order__created_at__month=today.month
    ).values('order').distinct().count()

    top_products = (
        Product.objects.filter(influencer=influencer)
        .annotate(
            total_sales=Sum('orderitem__quantity'),
            total_revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
        )
        .filter(total_sales__isnull=False)
        .select_related('category')
        .order_by('-total_sales')[:5]
    )

    # Get influencer's videos and products for the template
    videos = InfluencerVideo.objects.filter(influencer=request.user, is_active=True)
    products = Product.objects.filter(influencer=request.user)

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'monthly_revenue': monthly_revenue,
        'monthly_orders': monthly_orders,
        'top_products': top_products,
        'videos': videos,
        'products': products,
    }
    return render(request, 'influencer_dashboard.html', context)




@login_required
def edit_influencer_profile(request):
    if request.user.user_type != 'influencer':
        return redirect('home')

    profile, created = InfluencerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = InfluencerProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('influencer_dashboard')
    else:
        form = InfluencerProfileForm(instance=profile, user=request.user)

    return render(request, 'edit_profile.html', {'form': form})


@login_required
def view_influencer_profile(request):
    if request.user.user_type != 'influencer':
        return redirect('home')

    profile, created = InfluencerProfile.objects.get_or_create(user=request.user)
    return render(request, 'view_profile.html', {'profile': profile})


@login_required
def customer_dashboard(request):
    if request.user.user_type != 'customer':
        return redirect('login')

    influencers = InfluencerProfile.objects.filter(user__is_active=True).select_related('user')
    products = Product.objects.filter(stock__gt=0).select_related('category', 'influencer')[:12]
    categories = Category.objects.all()

    return render(request, 'customer_dashboard.html', {
        'influencers': influencers,
        'products': products,
        'categories': categories,
    })


def logout_view(request):
    logout(request)
    return redirect('home')


def list_influencers(request):
    profiles = InfluencerProfile.objects.filter(
        user__user_type='influencer',
        user__is_active=True
    ).select_related('user')
    return render(request, 'influencer_list.html', {'profiles': profiles})


def about_us(request):
    return render(request, 'about_us.html')


def view_influencer_detail(request, influencer_id):
    influencer = get_object_or_404(CustomUser, id=influencer_id, user_type='influencer', is_active=True)
    profile = getattr(influencer, 'influencer_profile', None)
    category_name = request.GET.get('category', 'All')
    categories = Category.objects.all()

    if category_name != 'All':
        category = get_object_or_404(Category, name__iexact=category_name)
        products = Product.objects.filter(influencer=influencer, category=category, stock__gt=0).select_related('category')
    else:
        products = Product.objects.filter(influencer=influencer, stock__gt=0).select_related('category')

    products_count = products.count()

    return render(request, 'influencer_detail.html', {
        'influencer': influencer,
        'profile': profile,
        'categories': categories,
        'selected_category': category_name,
        'products': products,
        'products_count': products_count
    })


@login_required
def featured_influencers(request):
    influencers = CustomUser.objects.filter(
        user_type='influencer',
        is_active=True
    ).select_related('influencer_profile').distinct()
    return render(request, 'featured_influencers.html', {'influencers': influencers})


def search_view(request):
    query = request.GET.get('q', '').strip()
    current_page = request.GET.get('page', '')

    if not query:
        if current_page == 'customer_dashboard':
            influencers = InfluencerProfile.objects.filter(user__is_active=True).select_related('user')
            products = Product.objects.filter(stock__gt=0).select_related('category', 'influencer')[:12]
            categories = Category.objects.all()
            return render(request, 'customer_dashboard.html', {
                'query': '',
                'influencers': influencers,
                'products': products,
                'categories': categories,
            })
        elif current_page == 'home':
            influencers = CustomUser.objects.filter(user_type='influencer')
            products = Product.objects.all().select_related('category', 'influencer')[:12]
            categories = Category.objects.all()
            return render(request, 'home.html', {
                'query': '',
                'influencers': influencers,
                'products': products,
                'categories': categories,
            })
        elif current_page == 'influencers':
            profiles = InfluencerProfile.objects.filter(user__is_active=True).select_related('user')
            return render(request, 'influencer_list.html', {'query': '', 'profiles': profiles})
        else:
            return render(request, 'search_results.html', {'query': ''})

    influencers = InfluencerProfile.objects.filter(
        Q(user__username__icontains=query) |
        Q(user__full_name__icontains=query) |
        Q(bio__icontains=query),
        user__is_active=True
    ).select_related('user')

    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query) |
        Q(influencer__username__icontains=query),
        stock__gt=0
    ).select_related('category', 'influencer')

    context = {
        'query': query,
        'influencers': influencers,
        'products': products,
        'categories': Category.objects.all(),
    }

    if current_page == 'customer_dashboard':
        return render(request, 'customer_dashboard.html', context)
    elif current_page == 'home':
        return render(request, 'home.html', context)
    elif current_page == 'influencers':
        return render(request, 'influencer_list.html', {'profiles': influencers, 'query': query})
    else:
        return render(request, 'search_results.html', context)



