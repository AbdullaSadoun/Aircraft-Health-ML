# preprocessing_ADAPT.py

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import logging
from datetime import datetime
import os 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ADAPTPreprocessor:
    def __init__(self, data_dir: str = "../data/ADAPT"):
        """
        Initialize ADAPT preprocessor
        
        Args:
            data_dir: Base directory for ADAPT data
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True) 
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Define sensor types based on paper
        self.sensor_prefixes = {
            'E': 'voltage',
            'ESH': 'relay_position',
            'ISH': 'current',
            'IT': 'temperature', 
            'LT': 'load',
            'ST': 'status',
            'TE': 'temperature'
        }
        
        # Known fault types from paper
        self.fault_types = {
            'StuckAt': 'stuck',
            'FailedOpen': 'failed_open',
            'FailedOff': 'failed_off',
            'Noise': 'noise',
            'Drift': 'drift'
        }

    def load_experiment(self, filename: str) -> pd.DataFrame:
        """
        Load a single ADAPT experiment file
        
        Args:
            filename: Name of experiment file
            
        Returns:
            DataFrame containing experiment data
        """
        try:
            file_path = self.raw_dir / filename
            
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found at {file_path}")
                
            # Read data with tab delimiter, skipping metadata
            df = pd.read_csv(file_path, delimiter='\t', skiprows=1, header=0, encoding='utf-8')  # Adjusted skiprows and header
            
            if 'Time' not in df.columns:
                # Try alternative column names
                time_columns = [col for col in df.columns if 'time' in col.lower()]
                if time_columns:
                    df.rename(columns={time_columns[0]: 'Time'}, inplace=True)
                else:
                    raise KeyError("No time column found in the data")
            
            # Convert time column dynamically
            df['Time'] = pd.to_datetime(df['Time'], errors='coerce')

            if df['Time'].isna().any():
                logger.warning(f"Some timestamps in {filename} could not be converted.")

            return df
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            raise

    def extract_fault_info(self, df: pd.DataFrame) -> Dict:
        """
        Extract fault injection information from experiment data
        
        Args:
            df: Raw experiment DataFrame
            
        Returns:
            Dictionary containing fault details
        """
        fault_info = {
            'time': None,
            'component': None, 
            'type': None,
            'location': None,
            'duration': None
        }
        
        # Find FaultInject rows
        fault_rows = df[df['SensorData'].str.contains('FaultInject', na=False)]
        
        if not fault_rows.empty:
            fault_row = fault_rows.iloc[0]
            
            # Extract fault information
            fault_info['time'] = pd.to_datetime(fault_row.get('Time', None), errors='coerce')
            fault_info['component'] = fault_row.get('FaultLocation', 'Unknown')
            fault_info['type'] = fault_row.get('FaultType', 'Unknown')
            fault_info['location'] = fault_row.get('FaultLocation', 'Unknown')
            
            # Calculate duration if experiment end time exists
            if not df.empty and fault_info['time']:
                fault_info['duration'] = (df['Time'].max() - fault_info['time']).total_seconds()
        
        return fault_info

    def process_sensor_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process sensor readings from experiment data
        
        Args:
            df: Raw experiment DataFrame
            
        Returns:
            DataFrame containing processed sensor data
        """
        sensor_data = df[df['SensorData'] == 'AntagonistData'].copy()

        sensor_cols = [col for col in sensor_data.columns if col.startswith('E')]
        processed_data = sensor_data[['Time'] + sensor_cols].copy()

        for col in sensor_cols:
            processed_data[col] = pd.to_numeric(processed_data[col], errors='coerce')
            processed_data[col] = processed_data[col].fillna(
                processed_data[col].rolling(5, min_periods=1).mean()
            )

        return processed_data

    def preprocess_experiment(self, filename: str) -> Optional[pd.DataFrame]:
        """
        Main preprocessing function for a single experiment
        
        Args:
            filename: Name of experiment file
            
        Returns:
            Processed sensor DataFrame or None if processing fails
        """
        try:
            logger.info(f"Processing file: {filename}")
            raw_df = self.load_experiment(filename)

            # Extract fault information
            fault_info = self.extract_fault_info(raw_df)

            # Process sensor data
            processed_df = self.process_sensor_data(raw_df)

            # Save processed data
            processed_path = self.processed_dir / f"processed_{filename.replace('.txt', '.csv')}"
            processed_df.to_csv(processed_path, index=False)

            # Save fault info
            fault_info_df = pd.DataFrame([fault_info])
            fault_info_path = self.processed_dir / f"fault_info_{filename.replace('.txt', '.csv')}"
            fault_info_df.to_csv(fault_info_path, index=False)

            logger.info(f"Processed data saved to {processed_path}")

            # Generate summary statistics for the individual experiment
            self.summarize_experiment(processed_df, filename)

            return processed_df
        except Exception as e:
            logger.error(f"Failed to preprocess {filename}: {e}")
            return None

    def summarize_experiment(self, processed_df: pd.DataFrame, filename: str) -> None:
        """
        Generate and save summary statistics for a single experiment.
        
        Args:
            processed_df: Processed DataFrame for the experiment.
            filename: Original filename of the experiment.
        """
        try:
            summary = processed_df.describe()
            summary_path = self.processed_dir / f"summary_{filename.replace('.txt', '.csv')}"
            summary.to_csv(summary_path)
            logger.info(f"Summary statistics for {filename} saved to {summary_path}")
        except Exception as e:
            logger.error(f"Failed to summarize {filename}: {e}")

    def preprocess_all_experiments(self) -> None:
        """Process all raw experiment files in the raw directory"""
        all_processed_data = []
        raw_files = list(self.raw_dir.glob('*.txt'))

        for file in raw_files:
            processed_data = self.preprocess_experiment(file.name)
            if processed_data is not None:
                all_processed_data.append(processed_data)
            else:
                logger.warning(f"Skipping {file.name} due to processing error.")

        if all_processed_data:
            self.summarize_statistics(all_processed_data)
        else:
            logger.warning("No valid data processed.")

    def summarize_statistics(self, all_processed_data: List[pd.DataFrame]) -> None:
        try:
            combined_data = pd.concat(all_processed_data, ignore_index=True)
            summary = combined_data.describe()
            summary_path = self.processed_dir / "summary_statistics.csv"
            summary.to_csv(summary_path)
            logger.info(f"Summary statistics saved to {summary_path}")
        except ValueError as e:
            logger.error(f"Failed to summarize statistics: {e}")

def main():
    """Main execution function"""
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_dir = os.path.join(project_root, "ml_models", "data", "ADAPT")
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    
    preprocessor = ADAPTPreprocessor(data_dir=data_dir)
    
    # Process all experiments and generate summary statistics
    preprocessor.preprocess_all_experiments()

if __name__ == "__main__":
    main()