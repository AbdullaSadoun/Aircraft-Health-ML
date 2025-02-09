# anomaly_detection.py

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from pathlib import Path
import logging
from typing import Dict, Tuple, List, Optional
import joblib
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ADAPTTimeSeriesDataset(Dataset):
    """Dataset class for ADAPT time series data"""
    
    def __init__(self, data: np.ndarray, sequence_length: int = 50):
        self.sequence_length = sequence_length
        self.data = torch.FloatTensor(data)
        
    def __len__(self):
        return len(self.data) - self.sequence_length + 1
        
    def __getitem__(self, idx):
        return self.data[idx:idx + self.sequence_length]

class MultiHeadAttention(nn.Module):
    """Multi-head attention module for temporal dependencies"""
    
    def __init__(self, input_dim: int, n_heads: int = 4):
        super().__init__()
        self.attention = nn.MultiheadAttention(input_dim, n_heads)
        
    def forward(self, x):
        x = x.transpose(0, 1)  # (seq_len, batch, features)
        attn_output, _ = self.attention(x, x, x)
        return attn_output.transpose(0, 1)  # (batch, seq_len, features)

class ADAPTAnomalyDetector(nn.Module):
    """Transformer-based anomaly detector for ADAPT data"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 64, n_heads: int = 4, n_layers: int = 2):
        super().__init__()
        self.input_dim = input_dim
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        self.time_embedding = nn.Linear(1, hidden_dim)
        self.attention_layers = nn.ModuleList([
            MultiHeadAttention(hidden_dim, n_heads) for _ in range(n_layers)
        ])
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.output_projection = nn.Linear(hidden_dim, input_dim)

    def forward(self, x, time_stamps):
        h = self.input_projection(x)
        t_emb = self.time_embedding(time_stamps.unsqueeze(-1))
        h += t_emb
        for attention in self.attention_layers:
            attended = attention(h)
            h = self.layer_norm(h + attended)
        return self.output_projection(h)

class NGAFIDAnomalyDetector:
    """Anomaly detector for NGAFID tabular data"""
    
    def __init__(self, contamination: float = 0.1):
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        
    def fit(self, data: pd.DataFrame):
        """Fit the NGAFID anomaly detector."""
        numerical_data = data.select_dtypes(include=[np.number])
        logger.info(f"Initial shape of numerical data: {numerical_data.shape}")
        
        # Replace infinities with NaN
        numerical_data.replace([np.inf, -np.inf], np.nan, inplace=True)
        logger.info("Replaced infinities with NaN")
        
        # Fill NaN values with median
        numerical_data.fillna(numerical_data.median(), inplace=True)
        logger.info("Filled NaN values with median")
        
        # Clip excessively large values to avoid overflow
        numerical_data = numerical_data.clip(lower=numerical_data.quantile(0.01), 
                                              upper=numerical_data.quantile(0.99), 
                                              axis=1)
        logger.info("Clipped outliers using 1% and 99% quantiles")
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(numerical_data)
        logger.info("Scaled numerical data")
        
        # Fit the Isolation Forest
        self.isolation_forest.fit(scaled_data)

    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Predict anomalies in NGAFID data"""
        numerical_data = data.select_dtypes(include=[np.number])
        scaled_data = self.scaler.transform(numerical_data)
        return self.isolation_forest.predict(scaled_data)

    def score_samples(self, data: pd.DataFrame) -> np.ndarray:
        """Return anomaly scores for NGAFID data"""
        numerical_data = data.select_dtypes(include=[np.number])
        scaled_data = self.scaler.transform(numerical_data)
        return -self.isolation_forest.decision_function(scaled_data)

class HybridAnomalyDetector:
    """Combined anomaly detector for both ADAPT and NGAFID data"""
    
    def __init__(self, 
                 adapt_input_dim: int,
                 sequence_length: int = 50,
                 hidden_dim: int = 64,
                 batch_size: int = 32,
                 learning_rate: float = 0.0001,  # Updated learning rate
                 n_epochs: int = 50,
                 contamination: float = 0.1):
        
        self.adapt_detector = ADAPTAnomalyDetector(adapt_input_dim, hidden_dim)
        self.ngafid_detector = NGAFIDAnomalyDetector(contamination)
        
        self.sequence_length = sequence_length
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.n_epochs = n_epochs
        
        self.adapt_scaler = StandardScaler()
        self.is_adapt = True  # Flag to track which detector to use
    
    def validate_data(self, data: pd.DataFrame):
        """Validate the data for infinite or excessively large values."""
        numerical_data = data.select_dtypes(include=[np.number])
        if numerical_data.isnull().any().any():
            raise ValueError("Data contains NaN values. Please preprocess the dataset.")
        if np.isinf(numerical_data.values).any():
            raise ValueError("Data contains infinity values. Please preprocess the dataset.")
        if (numerical_data.values > 1e6).any():
            raise ValueError("Data contains excessively large values. Please preprocess the dataset.")
    
    def fit_adapt(self, data: pd.DataFrame):
        """Train ADAPT anomaly detector"""
        # Validate data
        self.validate_data(data)
        
        # Scale data
        scaled_data = self.adapt_scaler.fit_transform(data)
        
        # Create dataset and dataloader
        dataset = ADAPTTimeSeriesDataset(scaled_data, self.sequence_length)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Training setup
        optimizer = torch.optim.Adam(self.adapt_detector.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()
        
        # Training loop
        for epoch in range(self.n_epochs):
            total_loss = 0
            for batch in dataloader:
                optimizer.zero_grad()
                output = self.adapt_detector(batch, torch.zeros(batch.size(0), 1))  # Placeholder for time_stamps
                loss = criterion(output, batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                
            avg_loss = total_loss / len(dataloader)
            if (epoch + 1) % 5 == 0:
                logger.info(f"ADAPT Epoch [{epoch+1}/{self.n_epochs}], Loss: {avg_loss:.4f}")
    
    def fit_ngafid(self, data: pd.DataFrame):
        """Train NGAFID anomaly detector"""
        # Validate data
        self.validate_data(data)
        
        self.ngafid_detector.fit(data)
    
    def detect_adapt_anomalies(self, data: pd.DataFrame, rolling_window: int = 50) -> np.ndarray:
        """Detect anomalies in ADAPT data using dynamic thresholding"""
        scaled_data = self.adapt_scaler.transform(data)
        dataset = ADAPTTimeSeriesDataset(scaled_data, self.sequence_length)
        dataloader = DataLoader(dataset, batch_size=self.batch_size)

        reconstruction_errors = []
        self.adapt_detector.eval()
        with torch.no_grad():
            for batch in dataloader:
                output = self.adapt_detector(batch, torch.zeros(batch.size(0), 1))  # Placeholder for time_stamps
                error = torch.mean((output - batch) ** 2, dim=(1, 2))
                reconstruction_errors.extend(error.numpy())

        reconstruction_errors = np.array(reconstruction_errors)
        rolling_mean = pd.Series(reconstruction_errors).rolling(rolling_window).mean()
        dynamic_threshold = rolling_mean + rolling_mean.std()
        return reconstruction_errors > dynamic_threshold.bfill().values
    
    def detect_ngafid_anomalies(self, data: pd.DataFrame) -> np.ndarray:
        """Detect anomalies in NGAFID data"""
        return self.ngafid_detector.predict(data) == -1
    
    def get_adapt_anomaly_scores(self, data: pd.DataFrame) -> np.ndarray:
        """Get anomaly scores for ADAPT data"""
        scaled_data = self.adapt_scaler.transform(data)
        dataset = ADAPTTimeSeriesDataset(scaled_data, self.sequence_length)
        dataloader = DataLoader(dataset, batch_size=self.batch_size)
        
        reconstruction_errors = []
        self.adapt_detector.eval()
        with torch.no_grad():
            for batch in dataloader:
                output = self.adapt_detector(batch, torch.zeros(batch.size(0), 1))  # Placeholder for time_stamps
                error = torch.mean((output - batch) ** 2, dim=(1, 2))
                reconstruction_errors.extend(error.numpy())
                
        return np.array(reconstruction_errors)
    
    def get_ngafid_anomaly_scores(self, data: pd.DataFrame) -> np.ndarray:
        """Get anomaly scores for NGAFID data"""
        return self.ngafid_detector.score_samples(data)
    
    def save_models(self, save_dir: str):
        """Save trained models"""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save ADAPT detector
        torch.save(self.adapt_detector.state_dict(), save_path / "adapt_detector.pth")
        joblib.dump(self.adapt_scaler, save_path / "adapt_scaler.joblib")
        
        # Save NGAFID detector
        joblib.dump(self.ngafid_detector, save_path / "ngafid_detector.joblib")
    
    def load_models(self, load_dir: str):
        """Load trained models"""
        load_path = Path(load_dir)
        
        # Load ADAPT detector
        self.adapt_detector.load_state_dict(torch.load(load_path / "adapt_detector.pth"))
        self.adapt_scaler = joblib.load(load_path / "adapt_scaler.joblib")
        
        # Load NGAFID detector
        self.ngafid_detector = joblib.load(load_path / "ngafid_detector.joblib")

    def save_detection_results(
        self, save_dir: str,
        adapt_data: pd.DataFrame,
        adapt_anomalies: np.ndarray,
        adapt_scores: np.ndarray,
        ngafid_data: pd.DataFrame,
        ngafid_anomalies: np.ndarray,
        ngafid_scores: np.ndarray
    ) -> None:
        """Save detection results for web visualization with detailed timelines"""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # Ensure timestamps are converted to strings
        time_strings = adapt_data['Time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

        # Format ADAPT results
        adapt_results = {
            'timeSeriesData': time_strings,
            'anomalies': adapt_anomalies.tolist(),
            'anomalyScores': adapt_scores.tolist(),
            'timeline': [
                {
                    'time': time_strings[i],
                    'score': float(adapt_scores[i]),  # Convert numpy float to Python float
                    'anomaly': bool(adapt_anomalies[i])
                }
                for i in range(len(adapt_anomalies))
            ],
            'summary': {
                'totalAnomalies': int(np.sum(adapt_anomalies)),
                'detectionRate': float((np.sum(adapt_anomalies) / len(adapt_anomalies)) * 100),
                'healthScore': float(100 - ((np.sum(adapt_anomalies) / len(adapt_anomalies)) * 100))
            }
        }

        # Format NGAFID results
        ngafid_results = {
            'flightData': ngafid_data.index.astype(str).tolist(),
            'anomalies': ngafid_anomalies.tolist(),
            'anomalyScores': [float(score) for score in ngafid_scores],  # Convert numpy floats to Python floats
            'summary': {
                'totalAnomalies': int(np.sum(ngafid_anomalies)),
                'detectionRate': float((np.sum(ngafid_anomalies) / len(ngafid_anomalies)) * 100),
                'healthScore': float(100 - ((np.sum(ngafid_anomalies) / len(ngafid_anomalies)) * 100))
            }
        }

        # Save results
        with open(save_path / 'adapt_results.json', 'w') as f:
            json.dump(adapt_results, f, ensure_ascii=False, indent=2)

        with open(save_path / 'ngafid_results.json', 'w') as f:
            json.dump(ngafid_results, f, ensure_ascii=False, indent=2)

        logger.info(f"Detection results saved to {save_path}")

    def fit(self, X, y=None):
        """Unified fit method for cross-validation"""
        if hasattr(X, 'shape') and len(X.shape) == 2:
            # For ADAPT data
            self.is_adapt = True
            self.fit_adapt(pd.DataFrame(X))
        else:
            # For NGAFID data
            self.is_adapt = False
            self.fit_ngafid(pd.DataFrame(X))
        return self

    def predict(self, X):
        """Unified predict method for cross-validation"""
        X_df = pd.DataFrame(X)
        if self.is_adapt:
            return self.detect_adapt_anomalies(X_df)
        else:
            return self.detect_ngafid_anomalies(X_df)

def load_adapt_data(data_dir: str) -> pd.DataFrame:
    """Load, combine, and resample all ADAPT processed files."""
    data_path = Path(data_dir)
    processed_files = list(data_path.glob("processed_*.csv"))

    all_data = []
    for file in processed_files:
        df = pd.read_csv(file)
        if 'Time' not in df.columns:
            logger.warning(f"'Time' column missing in file {file}. Skipping file.")
            continue
        df['Time'] = pd.to_datetime(df['Time'])
        df.set_index('Time', inplace=True)
        df = df.resample('1s').mean()  # Updated to lower-case 's'
        df.interpolate(method='linear', inplace=True)  # Interpolate missing values
        all_data.append(df)

    return pd.concat(all_data, ignore_index=False).reset_index()

def main():
    """Main execution function"""
    try:
        # Set paths
        base_dir = Path(".")
        adapt_data_dir = base_dir / "../data/ADAPT/processed"
        ngafid_data_path = base_dir / "../data/NGAFID/processed/processed_flight_header.csv"
        models_dir = base_dir / "models"
        results_dir = base_dir / "results"

        # Create directories
        models_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)

        # Load data
        logger.info("Loading data...")
        adapt_data = load_adapt_data(adapt_data_dir)
        ngafid_data = pd.read_csv(ngafid_data_path)
        if 'Time' not in adapt_data.columns:
            logger.warning("'Time' column missing in ADAPT dataset. Proceeding without time-based analysis.")

        # Initialize detector with updated learning rate
        adapt_input_dim = len(adapt_data.columns) - 1  # Exclude timestamp
        detector = HybridAnomalyDetector(adapt_input_dim=adapt_input_dim, learning_rate=1e-4)
        
        # Fine-tune learning rate in main()
        detector.fit_adapt(adapt_data.drop(columns=['Time'], errors='ignore'))
        detector.fit_ngafid(ngafid_data)

        # Detect anomalies with updated method
        logger.info("Detecting anomalies...")
        adapt_anomalies = detector.detect_adapt_anomalies(adapt_data.drop(columns=['Time'], errors='ignore'))
        adapt_scores = detector.get_adapt_anomaly_scores(adapt_data.drop(columns=['Time'], errors='ignore'))

        ngafid_anomalies = detector.detect_ngafid_anomalies(ngafid_data)
        ngafid_scores = detector.get_ngafid_anomaly_scores(ngafid_data)

        # Save models and results
        logger.info("Saving models and results...")
        detector.save_models(models_dir)
        detector.save_detection_results(
            results_dir,
            adapt_data,
            adapt_anomalies,
            adapt_scores,
            ngafid_data,
            ngafid_anomalies,
            ngafid_scores
        )

        logger.info("Training and detection complete!")
        logger.info(f"ADAPT anomalies detected: {np.sum(adapt_anomalies)}")
        logger.info(f"NGAFID anomalies detected: {np.sum(ngafid_anomalies)}")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()