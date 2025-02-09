import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from monitoring.models import Flight

class Command(BaseCommand):
    help = 'Load flight_header data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting data-loading process..."))  # Start log
        
        # Initialize counters
        processed_count_flights = 0
        skipped_count_flights = 0

        # Define the error log path
        error_log_path = 'flight_error_log.txt'  # Update error log path

        # Normalize headers
        def normalize_header(header):
            """Normalize header keys to remove spaces and ensure consistent casing."""
            return header.strip().replace(' ', '_').lower()

        # Process flight_header.csv directly
        with open(Path('monitoring/ml_models/data/NGAFID/raw/flight_header.csv'), 'r') as file:
            reader = csv.DictReader(file)
            reader.fieldnames = [normalize_header(col) for col in reader.fieldnames]  # Normalize headers
            self.stdout.write(f"Normalized CSV Headers: {reader.fieldnames}")  # Debugging log

            # Check for required columns
            required_columns = ['master_index', 'before_after', 'date_diff', 'flight_length', 'label', 'number_flights_before']
            missing_columns = [col for col in required_columns if col not in reader.fieldnames]
            if missing_columns:
                self.stderr.write(self.style.ERROR(f"Missing required columns: {missing_columns}"))
                return

            for row in reader:
                self.stdout.write(f"Raw row data: {row}")  # Log raw row data
                try:
                    master_index = int(row['master_index'])
                    date_diff = int(float(row['date_diff']))
                    flight_length = int(float(row['flight_length']))
                    number_flights_before = int(float(row['number_flights_before']))
                    
                    # Log the casted values for debugging
                    self.stdout.write(f"Processing Flight {master_index}: flight_length={flight_length}, date_diff={date_diff}, number_flights_before={number_flights_before}")

                    flight, created = Flight.objects.update_or_create(
                        master_index=master_index,
                        defaults={
                            'before_after': row['before_after'],
                            'date_diff': date_diff,
                            'flight_length': flight_length,
                            'label': row['label'],
                            'hierarchy': row.get('hierarchy', ''),
                            'number_flights_before': number_flights_before
                        }
                    )
                    processed_count_flights += 1  # Increment processed flights
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created Flight {flight.master_index}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Updated Flight {flight.master_index}"))
                except ValueError as e:
                    skipped_count_flights += 1  # Increment skipped flights
                    self.stderr.write(self.style.ERROR(f"Skipping row {row}: {e}"))
                    
                    # Log invalid rows to a file
                    with open(error_log_path, 'a') as log_file:
                        log_file.write(f"Invalid row: {row}, Error: {e}\n")
                    continue

        self.stdout.write(self.style.SUCCESS(f"Processed {processed_count_flights} Flights"))
        self.stdout.write('Data loaded successfully')
        self.stderr.write(self.style.ERROR(f"Skipped {skipped_count_flights} rows due to errors"))

        # Summary Logs
        self.stdout.write(self.style.SUCCESS(f"Total flights processed: {processed_count_flights}"))
        self.stdout.write(self.style.ERROR(f"Total flights skipped: {skipped_count_flights}"))
        self.stdout.write(self.style.SUCCESS("Data-loading process completed."))

        # Metrics reporting
        self.stdout.write(self.style.SUCCESS("Data loading complete"))
        self.stdout.write(self.style.SUCCESS(f"Total records processed: {processed_count_flights + skipped_count_flights}"))
        self.stdout.write(self.style.SUCCESS(f"Total records inserted/updated: {processed_count_flights}"))
        self.stdout.write(self.style.ERROR(f"Total records skipped: {skipped_count_flights}"))
        self.stdout.write(self.style.SUCCESS(f"Error log written to {error_log_path}"))