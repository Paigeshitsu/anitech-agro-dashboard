from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    # Main market view
    path('', views.market_view, name='market'),
    
    # Market Prices
    path('prices/', views.price_list, name='price_list'),
    path('prices/add/', views.price_add, name='price_add'),
    path('prices/<int:price_id>/edit/', views.price_edit, name='price_edit'),
    path('prices/<int:price_id>/delete/', views.price_delete, name='price_delete'),
    
    # Buyer Offers
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/add/', views.offer_add, name='offer_add'),
    path('offers/<int:offer_id>/edit/', views.offer_edit, name='offer_edit'),
    path('offers/<int:offer_id>/delete/', views.offer_delete, name='offer_delete'),
    path('offers/<int:offer_id>/status/', views.offer_update_status, name='offer_update_status'),
    
    # Schedule Distributions
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/add/', views.schedule_add, name='schedule_add'),
    path('schedules/<int:schedule_id>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:schedule_id>/delete/', views.schedule_delete, name='schedule_delete'),
    
    # Buyer Dashboard (legacy)
    path('buyer-dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    
    # Seller Offers (legacy symmetric)
    path('sell-offers/', views.seller_offer_list, name='seller_offer_list'),
    path('sell-offers/add/', views.seller_offer_add, name='seller_offer_add'),
    path('sell-offers/<int:offer_id>/edit/', views.seller_offer_edit, name='seller_offer_edit'),
    path('sell-offers/<int:offer_id>/delete/', views.seller_offer_delete, name='seller_offer_delete'),
    path('sell-offers/<int:offer_id>/status/', views.seller_offer_update_status, name='seller_offer_update_status'),
]

