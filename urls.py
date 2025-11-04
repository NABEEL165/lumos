from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('my-products/', views.influencer_product_list, name='influencer_product_list'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('influencer/<int:influencer_id>/products/', views.influencer_products, name='view_influencer_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/review/', views.add_review, name='add_review'),
    path('sold-products/',views.influencer_sold_products, name='influencer_sold_products'),

    # path('sold-products/', views.sold_products_view, name='influencer_sold_products')

    # path('influencer/<int:influencer_id>/products/', views.product_list, name='product_list'),

    path('products/', views.product_lists, name='product_lists'),
    path('add-category/', views.add_category, name='add_category'),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
