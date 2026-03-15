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
    path('director/', views.director_dashboard, name='director_dashboard'),

    # Document CRUD
    path('documents/', views.document_list, name='document_list'),
    path('add/', views.document_add, name='document_add'),
    path('detail/<int:pk>/', views.document_detail, name='detail'),
    path('edit/<int:pk>/', views.document_edit, name='edit'),
    path('delete/<int:pk>/', views.document_delete, name='delete'),
    path('download/<int:pk>/', views.download_file, name='download_file'),

    # Workflow
    path('send-to-director/<int:pk>/', views.send_to_director, name='send_to_director'),
    path('sign/<int:pk>/', views.sign_document, name='sign_document'),
    path('forward/<int:pk>/', views.forward_document, name='forward_document'),
    path('receive/<int:route_id>/', views.receive_document, name='receive_document'),

    # Notification
    path('notification/read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),

    path('view/<str:pk>/', views.view_file, name='view_file'),

    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/edit/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/delete/<int:pk>/', views.UserDeleteView.as_view(), name='user_delete'),

    path('password_reset/',auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),name='password_reset'),
    path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(
    template_name='registration/password_reset_done.html'),
    name='password_reset_done'
    ),
]
