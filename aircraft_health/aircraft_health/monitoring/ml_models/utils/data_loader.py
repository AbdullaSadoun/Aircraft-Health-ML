# utils/data_loader.py

import pandas as pd
import json
from pathlib import Path

class ADAPTDataLoader:
    def __init__(self, processed_dir: str):
        self.processed_dir = Path(processed_dir)
        
    def get_experiment_list(self):
        """Get list of all processed experiments"""
        return [f.stem.replace('processed_', '') 
                for f in self.processed_dir.glob('processed_*.csv')]
    
    def load_experiment(self, experiment_id: str):
        """Load processed experiment data and fault info"""
        sensor_data = pd.read_csv(self.processed_dir / f'processed_{experiment_id}.csv')
        fault_info = pd.read_csv(self.processed_dir / f'fault_info_{experiment_id}.csv')
        
        return {
            'sensor_data': sensor_data.to_dict('records'),
            'fault_info': fault_info.to_dict('records')[0]
        }