import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder, StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.impute import SimpleImputer
import os
import logging

def load_data(filepath):
    """
    Load the NGAFID dataset from a CSV file.
    """
    data = pd.read_csv(filepath)
    logging.info("Data Loaded Successfully!")
    logging.info(data.info())
    return data

def handle_missing_values(data, intermediate_dir):
    """
    Handle missing values based on data types.
    """
    logging.info("Handling missing values...")
    
    # Log missing values percentage
    missing_info = data.isnull().mean() * 100
    logging.info(f"Missing values percentage:\n{missing_info}")
    
    numerical_columns = data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = data.select_dtypes(include=['object']).columns.tolist()
    
    # Impute numerical columns with mean
    num_imputer = SimpleImputer(strategy="mean")
    data[numerical_columns] = num_imputer.fit_transform(data[numerical_columns])
    
    # Handle 'hierarchy' with mapping based on 'label'
    hierarchy_map = {
        "intake gasket leak/damage": "engine",
        # Add mappings for other labels
    }
    if 'label' in data.columns:
        data['hierarchy'] = data['label'].map(hierarchy_map).fillna("unknown")
    else:
        logging.warning("'label' column is missing. Imputing 'hierarchy' with overall mode.")
        cat_imputer = SimpleImputer(strategy="most_frequent")
        data[categorical_columns] = cat_imputer.fit_transform(data[categorical_columns])
    
    # Log missing values after imputation
    missing_info_after = data.isnull().mean() * 100
    logging.info(f"Missing values after imputation:\n{missing_info_after}")
    
    # Save intermediate result
    data.to_csv(os.path.join(intermediate_dir, "after_missing_values.csv"), index=False)
    logging.info("Saved data after handling missing values.")
    
    return data

def handle_outliers(data, intermediate_dir):
    """
    Detect and remove outliers in 'flight_length' using IQR.
    """
    logging.info("Detecting and handling outliers in 'flight_length'...")
    Q1 = data['flight_length'].quantile(0.25)
    Q3 = data['flight_length'].quantile(0.75)
    IQR = Q3 - Q1
    data = data[(data['flight_length'] >= Q1 - 1.5 * IQR) & (data['flight_length'] <= Q3 + 1.5 * IQR)]
    logging.info("Outliers removed based on IQR method.")
    
    # Save intermediate result
    data.to_csv(os.path.join(intermediate_dir, "after_outliers.csv"), index=False)
    logging.info("Saved data after handling outliers.")
    
    return data

def encode_labels(data, intermediate_dir):
    """
    Encode categorical columns using LabelEncoder.
    """
    logging.info("Encoding labels with LabelEncoder...")
    label_encoder = LabelEncoder()
    if 'label' in data.columns:
        data['label_encoded'] = label_encoder.fit_transform(data['label'])
    else:
        raise KeyError("'label' column is missing from the dataset.")
    
    # Log label mappings
    label_mapping = {class_label: index for index, class_label in enumerate(label_encoder.classes_)}
    logging.info(f"Label mapping:\n{label_mapping}")
    
    # Save intermediate result
    data.to_csv(os.path.join(intermediate_dir, "after_label_encoding.csv"), index=False)
    logging.info("Saved data after encoding labels.")
    
    return data, label_encoder

def normalize_features(data, columns_to_normalize, method, intermediate_dir):
    """
    Normalize numeric columns using the specified method.
    """
    logging.info(f"Normalizing features using {method} scaler...")
    
    # Apply log transformation to 'date_diff' if present
    if 'date_diff' in data.columns:
        logging.info("Applying log transformation to 'date_diff' to handle skewed distribution.")
        data['date_diff'] = np.log1p(data['date_diff'])
    else:
        logging.warning("'date_diff' column is missing. Skipping log transformation.")
    
    # Handle infinite or large values
    data[columns_to_normalize] = data[columns_to_normalize].replace([np.inf, -np.inf], np.nan)
    
    # Impute missing values after handling infinite or large values
    imputer = SimpleImputer(strategy="mean")
    data[columns_to_normalize] = imputer.fit_transform(data[columns_to_normalize])
    
    if method == "standard":
        scaler = StandardScaler()
    elif method == "minmax":
        scaler = MinMaxScaler()
    else:
        raise ValueError("Unsupported scaling method")
    
    data[columns_to_normalize] = scaler.fit_transform(data[columns_to_normalize])
    
    # Log feature distributions
    logging.info(f"Feature distributions after {method} scaling:\n{data[columns_to_normalize].describe()}")
    
    # Save intermediate result
    data.to_csv(os.path.join(intermediate_dir, "after_normalization.csv"), index=False)
    logging.info("Saved data after normalization.")
    
    return data, scaler

def feature_engineering(data, intermediate_dir):
    """
    Add new features and transformations.
    """
    logging.info("Performing feature engineering...")
    
    # Check if required columns exist
    required_columns = ['label', 'flight_length']
    for col in required_columns:
        if col not in data.columns:
            raise KeyError(f"'{col}' column is missing from the dataset.")
    
    logging.info(f"Unique values in 'label': {data['label'].unique()}")
    logging.info(f"Value counts in 'hierarchy':\n{data['hierarchy'].value_counts()}")
    
    # Mean flight length per label
    data['mean_flight_length_per_label'] = data.groupby('label')['flight_length'].transform('mean')
    
    # Time-based feature
    data['is_recent_flight'] = data['date_diff'].apply(lambda x: 1 if x > 0 else 0)
    
    # Add ratio of flight length to number of previous flights
    data['flight_length_ratio'] = data['flight_length'] / (data['number_flights_before'] + 1)
    
    # Handle 'inf' values in 'flight_length_ratio'
    data['flight_length_ratio'].replace([np.inf, -np.inf], np.nan, inplace=True)
    data['flight_length_ratio'].fillna(data['flight_length_ratio'].mean(), inplace=True)
    
    # Add new features
    data['flights_per_length'] = data['number_flights_before'] / (data['flight_length'] + 1)
    data['before_after_date_diff'] = data['before_after'] * data['date_diff']
    
    logging.info("Feature engineering complete!")
    
    # Save intermediate result
    data.to_csv(os.path.join(intermediate_dir, "after_feature_engineering.csv"), index=False)
    logging.info("Saved data after feature engineering.")
    
    return data

def split_data(data, target_column):
    """
    Split data into train and test sets with stratified sampling.
    """
    logging.info("Splitting data into train and test sets with stratification...")
    X = data.drop(columns=[target_column, 'Master Index'])
    y = data[target_column]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    logging.info("Train/Test split complete!")
    logging.info(f"Train distribution:\n{y_train.value_counts(normalize=True)}")
    logging.info(f"Test distribution:\n{y_test.value_counts(normalize=True)}")
    
    return X_train, X_test, y_train, y_test

def preprocess_ngafid(filepath, target_column, columns_to_normalize, normalization_method="standard"):
    """
    Full preprocessing pipeline for NGAFID data.
    """
    logging.info("Starting preprocessing pipeline...")
    data = load_data(filepath)
    
    intermediate_dir = os.path.join(os.path.dirname(filepath), "intermediate")
    os.makedirs(intermediate_dir, exist_ok=True)
    
    data = handle_missing_values(data, intermediate_dir)
    data = handle_outliers(data, intermediate_dir)
    data = feature_engineering(data, intermediate_dir)  # Ensure proper handling of missing columns
    
    # Clip negative values for 'number_flights_before'
    if 'number_flights_before' in data.columns:
        data['number_flights_before'] = data['number_flights_before'].clip(lower=0)
    else:
        logging.warning("'number_flights_before' column is missing. Skipping clipping.")
    
    data, encoder = encode_labels(data, intermediate_dir)  # Ensure 'label' column exists
    
    if columns_to_normalize:
        valid_columns = [col for col in columns_to_normalize if col in data.columns]
        data, scaler = normalize_features(data, valid_columns, method=normalization_method, intermediate_dir=intermediate_dir)
    else:
        logging.warning("No columns specified for normalization. Skipping normalization.")
    
    X_train, X_test, y_train, y_test = split_data(data, target_column)
    
    # Save final processed data
    processed_dir = os.path.join(os.path.dirname(filepath), "processed")
    os.makedirs(processed_dir, exist_ok=True)
    data.to_csv(os.path.join(processed_dir, "final_processed_data.csv"), index=False)
    logging.info("Saved final processed data.")
    
    logging.info("Preprocessing pipeline completed.")
    return X_train, X_test, y_train, y_test, encoder, scaler, data

if __name__ == "__main__":
    # Main execution function
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    data_dir = os.path.join(project_root, "ml_models",  "data", "NGAFID", "raw")
    processed_data_dir = os.path.join(project_root, "ml_models","data", "NGAFID",  "processed")
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Processed data directory: {processed_data_dir}")
    
    filepath = os.path.join(data_dir, "flight_header.csv")
    
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
    else:
        target_column = "label_encoded"
        columns_to_normalize = ['flight_length', 'number_flights_before', 'date_diff']
        
        X_train, X_test, y_train, y_test, encoder, scaler, processed_data = preprocess_ngafid(
            filepath, target_column, columns_to_normalize, normalization_method="minmax"
        )
        
        # Save the processed data
        os.makedirs(processed_data_dir, exist_ok=True)
        processed_filepath = os.path.join(processed_data_dir, "processed_flight_header.csv")
        processed_data.to_csv(processed_filepath, index=False)
        
        logger.info(f"Processed data saved to: {processed_filepath}")
