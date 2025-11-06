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
