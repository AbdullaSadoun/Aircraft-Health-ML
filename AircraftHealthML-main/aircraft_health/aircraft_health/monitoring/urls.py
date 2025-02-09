from django.urls import path, re_path
from .views import FlightListView, FlightDetailView
from . import views

urlpatterns = [
    path('api/experiments/', views.get_experiment_list, name='experiment-list'),
    path('api/experiments/<str:experiment_id>/', views.get_experiment_data, name='experiment-data'),
    path('api/ngafid/flight_data/', FlightListView.as_view(), name='flight-list'),
    path('api/ngafid/flight_data/<int:flight_id>/', FlightDetailView.as_view(), name='flight-detail'),
    path('api/ngafid/flights_by_label/<str:label>/', views.flights_by_label, name='flights-by-label'),
    path('api/ngafid/unique_labels/', views.unique_labels, name='unique-labels'),
    path('api/ngafid/grouped_flight_data/', views.grouped_flight_data, name='grouped-flight-data'),
    path('api/ngafid/preprocessed_flight_data/', views.preprocessed_flight_data, name='preprocessed-flight-data'),
    path('api/anomaly-detection/results/', views.get_anomaly_results, name='get_anomaly_results'),
    path('api/anomaly-detection/threshold/', views.update_threshold, name='update_threshold'),
    path('api/anomaly-detection/historical/', views.get_historical_data, name='get_historical_data'),
    re_path(r'^.*$', views.dashboard_view, name='dashboard'),
]