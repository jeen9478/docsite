from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', auth_views.LoginView.as_view(
        template_name='login.html'
    ), name='login'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('inbox/', views.inbox_dashboard, name='inbox_dashboard'),
    path('dept-inbox/', views.inbox, name='dept_inbox'),
    path('director/', views.director_dashboard, name='director_dashboard'),

    # Document CRUD
    path('documents/', views.document_list, name='document_list'),
    path('search/', views.doc_list, name='doc_list'),
    path('add/', views.document_add, name='document_add'),
    path('detail/<str:pk>/', views.document_detail, name='detail'),
    path('edit/<str:pk>/', views.document_edit, name='edit'),
    path('delete/<str:pk>/', views.document_delete, name='delete'),
    path('download/<str:doc_no>/', views.download_file, name='download_file'),

    # Workflow
    path('send-to-director/<str:doc_no>/', views.send_to_director, name='send_to_director'),
    path('sign/<str:doc_no>/', views.sign_document, name='sign_document'),
    path('forward/<str:doc_no>/', views.forward_document, name='forward_document'),
    path('receive/<int:route_id>/', views.receive_document, name='receive_document'),

    # Notification
    path('notification/read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),

    path('view/<int:pk>/', views.view_file, name='view_file'),

]
