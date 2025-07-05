from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'checklists',views.ChecklistViewSet)
router.register(r'items', views.ChecklistItemViewSet)
router.register(r'submissions', views.ChecklistItemSubmissionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('checklistitem/start/<int:user_id>/<int:item_id>/', views.StartChecklistItemAPIView.as_view()),
    path('checklistitems/inprogress/<int:user_id>/', views.ChecklistItemInProgressByUserView.as_view()),
    path('checklistitems/completed/<int:user_id>/', views.ChecklistItemCompletedByUserView.as_view()),
    path('checklistitems/by-category-status/<int:cat_or_subcat_id>/', views.ChecklistItemByCategoryStatusView.as_view()),

]
