from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Autenticación
    path("login/", views.LoginVista.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("registro/", views.registro, name="registro"),

    # Dashboard
    path("", views.inicio, name="inicio"),

    # Módulos especiales (antes del CRUD genérico)
    path("agenda/", views.agenda, name="agenda"),
    path("crm/", views.crm, name="crm"),
    path("pacientes/<int:pk>/ficha/", views.ficha, name="ficha"),
    path("pacientes/<int:pk>/odontograma/", views.odontograma, name="odontograma"),
    path("recetas/<int:pk>/imprimir/", views.receta_imprimir, name="receta_imprimir"),

    # Reportes (antes del CRUD para que "reportes" no se tome como módulo)
    path("reportes/<slug:tipo>/", views.reporte, name="reporte"),
    path("reportes/<slug:tipo>/imprimir/", views.impresion, name="impresion"),

    # CRUD genérico de los modelos: /pacientes/, /citas/, /recetas/, ...
    path("<slug:modulo>/", views.listado, name="listado"),
    path("<slug:modulo>/nuevo/", views.formulario, name="crear"),
    path("<slug:modulo>/<int:pk>/editar/", views.formulario, name="editar"),
    path("<slug:modulo>/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
]
