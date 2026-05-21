from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("teach/<slug:slug>/builder/", views.course_builder, name="course_builder"),
    path("teach/<slug:slug>/modules/add/", views.add_module, name="add_module"),
    path("teach/<slug:slug>/modules/reorder/", views.reorder_modules, name="reorder_modules"),
    path("teach/modules/<uuid:module_id>/lessons/add/", views.add_lesson, name="add_lesson"),
    path("teach/modules/<uuid:module_id>/lessons/reorder/", views.reorder_lessons, name="reorder_lessons"),
    path("teach/modules/<uuid:module_id>/delete/", views.delete_module, name="delete_module"),
    path("teach/lessons/<uuid:lesson_id>/items/add/", views.add_item, name="add_item"),
    path("teach/lessons/<uuid:lesson_id>/delete/", views.delete_lesson, name="delete_lesson"),
    path("teach/items/<uuid:item_id>/delete/", views.delete_item, name="delete_item"),
]
