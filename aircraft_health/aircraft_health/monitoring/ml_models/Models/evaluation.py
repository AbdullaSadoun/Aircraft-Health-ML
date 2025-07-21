# evaluation.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple, List, Optional
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, 
    roc_curve, precision_recall_curve, average_precision_score,
    f1_score, matthews_corrcoef
)
from sklearn.model_selection import KFold, TimeSeriesSplit
import logging
from pathlib import Path
import json
from datetime import datetime
from anomaly_detection import HybridAnomalyDetector  # Ensure this import is correct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyEvaluator:
    def __init__(self, output_dir: Optional[str] = None):
        self.metrics = {}
        self.output_dir = Path(output_dir) if output_dir else Path("evaluation_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to [0,1] range"""
        scores = np.array(scores)
        if scores.max() == scores.min():
            return np.zeros_like(scores)
        return (scores - scores.min()) / (scores.max() - scores.min())
    
    def find_optimal_threshold(self, y_true: np.ndarray, scores: np.ndarray, 
                             method: str = 'f1') -> float:
        """Find optimal threshold using various methods"""
        scores = self.normalize_scores(scores)
        thresholds = np.linspace(0, 1, 100)
        best_metric = 0
        best_threshold = 0.5
        
        for threshold in thresholds:
            y_pred = (scores > threshold).astype(int)
            
            if method == 'f1':
                metric = f1_score(y_true, y_pred)
            elif method == 'mcc':
                metric = matthews_corrcoef(y_true, y_pred)
            elif method == 'balanced':
                tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
                specificity = tn / (tn + fp)
                sensitivity = tp / (tp + fn)
                metric = (specificity + sensitivity) / 2
            
            if metric > best_metric:
                best_metric = metric
                best_threshold = threshold
        
        return best_threshold
    
    def cross_validate(self, anomaly_detector, X: np.ndarray, y: np.ndarray, 
                      n_splits: int = 5, time_series: bool = True) -> Dict:
        """Perform cross-validation"""
        cv = TimeSeriesSplit(n_splits=n_splits) if time_series else KFold(n_splits=n_splits, shuffle=True)
        
        cv_scores = {
            'roc_auc': [], 'f1': [], 'precision': [], 'recall': [], 'mcc': []
        }
        
        for fold, (train_idx, test_idx) in enumerate(cv.split(X)):
            try:
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                
                logger.info(f"Training fold {fold+1}")
                anomaly_detector.fit(X_train)
                
                scores = anomaly_detector.predict(X_test)
                scores = self.normalize_scores(scores)
                
                # Find optimal threshold
                threshold = self.find_optimal_threshold(y_test, scores)
                y_pred = (scores > threshold).astype(int)
                
                # Calculate metrics
                cv_scores['roc_auc'].append(roc_auc_score(y_test, scores))
                cv_scores['f1'].append(f1_score(y_test, y_pred))
                p, r, _ = precision_recall_curve(y_test, scores)
                cv_scores['precision'].append(p.mean())
                cv_scores['recall'].append(r.mean())
                cv_scores['mcc'].append(matthews_corrcoef(y_test, y_pred))
                
                logger.info(f"Fold {fold+1} Results:")
                logger.info(f"ROC-AUC: {cv_scores['roc_auc'][-1]:.3f}")
                logger.info(f"F1-Score: {cv_scores['f1'][-1]:.3f}")
                logger.info(f"MCC: {cv_scores['mcc'][-1]:.3f}")
            
            except Exception as e:
                logger.error(f"Error in fold {fold+1}: {str(e)}")
                continue
        
        return cv_scores
    
    def evaluate(self, y_true: np.ndarray, scores: np.ndarray, 
                threshold: Optional[float] = None, dataset_name: str = "",
                save_results: bool = True) -> Dict:
        """Comprehensive evaluation of anomaly detection results"""
        # Convert inputs to numpy arrays
        y_true = np.array(y_true)
        scores = self.normalize_scores(scores)
        
        if threshold is None:
            threshold = self.find_optimal_threshold(y_true, scores)
        
        # Calculate metrics
        y_pred = (scores > threshold).astype(int)
        self.metrics[dataset_name] = self._calculate_metrics(y_true, y_pred, scores)
        
        # Generate visualizations
        self._plot_confusion_matrix(y_true, y_pred, dataset_name)
        self._plot_roc_curve_safe(y_true, scores, dataset_name)
        self._plot_precision_recall_safe(y_true, scores, dataset_name)
        self._plot_score_distributions(scores, y_true, dataset_name)
        self._plot_threshold_sensitivity(y_true, scores, dataset_name)
        
        if save_results:
            self._save_results(dataset_name)
        
        return self.metrics[dataset_name]
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, 
                         scores: np.ndarray) -> Dict:
        """Calculate all evaluation metrics"""
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        return {
            'confusion_matrix': confusion_matrix(y_true, y_pred),
            'classification_report': classification_report(y_true, y_pred, output_dict=True),
            'roc_auc': roc_auc_score(y_true, scores),
            'average_precision': average_precision_score(y_true, scores),
            'mcc': matthews_corrcoef(y_true, y_pred),
            'specificity': tn / (tn + fp),
            'sensitivity': tp / (tp + fn),
            'precision': tp / (tp + fp),
            'recall': tp / (tp + fn),
            'f1': f1_score(y_true, y_pred)
        }
    
    def _plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray, dataset_name: str):
        """Plot confusion matrix"""
        cm = confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['Normal', 'Anomaly'],
                   yticklabels=['Normal', 'Anomaly'])
        
        # Add percentage annotations
        total = np.sum(cm)
        for i in range(2):
            for j in range(2):
                plt.text(j + 0.5, i + 0.7, f'({cm[i,j]/total*100:.1f}%)',
                        ha='center', va='center')
        
        plt.title(f'Confusion Matrix - {dataset_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        self._save_plot(f'confusion_matrix_{dataset_name}')
    
    def _plot_roc_curve_safe(self, y_true: np.ndarray, scores: np.ndarray, dataset_name: str):
        """Plot ROC curve with safe threshold annotations"""
        fpr, tpr, thresholds = roc_curve(y_true, scores)
        roc_auc = self.metrics[dataset_name]['roc_auc']
        
        plt.figure(figsize=(10, 8))
        plt.plot(fpr, tpr, label=f'ROC curve (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        
        # Safely add threshold annotations
        step = max(1, len(thresholds) // 5)
        for i in range(0, len(thresholds), step):
            plt.annotate(f'θ={thresholds[i]:.2f}',
                         (fpr[i], tpr[i]),
                         textcoords="offset points",
                         xytext=(0, 10),
                         ha='center')
        
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {dataset_name}')
        plt.legend()
        plt.grid(True)
        self._save_plot(f'roc_curve_{dataset_name}')
    
    def _plot_precision_recall_safe(self, y_true: np.ndarray, scores: np.ndarray, dataset_name: str):
        """Plot Precision-Recall curve"""
        precision, recall, _ = precision_recall_curve(y_true, scores)
        avg_precision = self.metrics[dataset_name]['average_precision']
        
        plt.figure(figsize=(10, 8))
        plt.plot(recall, precision, 
                label=f'PR curve (AP = {avg_precision:.3f})')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title(f'Precision-Recall Curve - {dataset_name}')
        plt.legend()
        plt.grid(True)
        self._save_plot(f'precision_recall_{dataset_name}')
    
    def _plot_score_distributions(self, scores: np.ndarray, y_true: np.ndarray, dataset_name: str):
        """Plot score distributions for normal vs anomaly classes"""
        plt.figure(figsize=(10, 8))
        
        # Plot distributions
        sns.kdeplot(scores[y_true == 0], label='Normal', fill=True)
        sns.kdeplot(scores[y_true == 1], label='Anomaly', fill=True)
        
        # Add threshold line
        if dataset_name in self.metrics:
            threshold = self.find_optimal_threshold(y_true, scores)
            plt.axvline(threshold, color='r', linestyle='--',
                       label=f'Optimal Threshold ({threshold:.3f})')
        
        plt.xlabel('Anomaly Score')
        plt.ylabel('Density')
        plt.title(f'Score Distributions - {dataset_name}')
        plt.legend()
        plt.grid(True)
        self._save_plot(f'score_distributions_{dataset_name}')
    
    def _plot_threshold_sensitivity(self, y_true: np.ndarray, scores: np.ndarray, dataset_name: str):
        """Plot sensitivity of metrics to threshold selection"""
        thresholds = np.linspace(0, 1, 100)
        metrics = {'F1': [], 'MCC': [], 'Precision': [], 'Recall': []}
        
        for threshold in thresholds:
            y_pred = (scores > threshold).astype(int)
            metrics['F1'].append(f1_score(y_true, y_pred))
            metrics['MCC'].append(matthews_corrcoef(y_true, y_pred))
            p, r, _ = precision_recall_curve(y_true, scores)
            metrics['Precision'].append(p[0])
            metrics['Recall'].append(r[0])
        
        plt.figure(figsize=(10, 8))
        for metric_name, values in metrics.items():
            plt.plot(thresholds, values, label=metric_name)
        
        optimal_threshold = self.find_optimal_threshold(y_true, scores)
        plt.axvline(optimal_threshold, color='r', linestyle='--',
                   label=f'Optimal Threshold ({optimal_threshold:.3f})')
        
        plt.xlabel('Threshold')
        plt.ylabel('Metric Value')
        plt.title(f'Threshold Sensitivity - {dataset_name}')
        plt.legend()
        plt.grid(True)
        self._save_plot(f'threshold_sensitivity_{dataset_name}')
    
    def _save_plot(self, name: str):
        """Save plot to output directory"""
        plt.savefig(self.output_dir / f"{name}.png", bbox_inches='tight', dpi=300)
        plt.close()
    
    def _save_results(self, dataset_name: str):
        """Save evaluation results to JSON"""
        results = {k: v if not isinstance(v, np.ndarray) else v.tolist() 
                  for k, v in self.metrics[dataset_name].items()}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(self.output_dir / f"metrics_{dataset_name}_{timestamp}.json", 'w') as f:
            json.dump(results, f, indent=4)
    
    def print_summary(self, dataset_name: str):
        """Print a summary of evaluation metrics for a given dataset"""
        metrics = self.metrics.get(dataset_name, {})
        if not metrics:
            logger.error(f"No metrics found for dataset: {dataset_name}")
            return
        
        print(f"Confusion Matrix for {dataset_name}:")
        print(metrics['confusion_matrix'])
        
        print("\nClassification Report:")
        for label, report in metrics['classification_report'].items():
            if isinstance(report, dict):
                print(f"{label}:")
                for metric, value in report.items():
                    print(f"  {metric}: {value:.3f}")
            else:
                print(f"{label}: {report:.3f}")
        
        print("\nAdditional Metrics:")
        print(f"ROC-AUC Score: {metrics['roc_auc']:.3f}")
        print(f"Average Precision Score: {metrics['average_precision']:.3f}")
        print(f"Matthews Correlation Coefficient: {metrics['mcc']:.3f}")
        print(f"Specificity: {metrics['specificity']:.3f}")
        print(f"Sensitivity: {metrics['sensitivity']:.3f}")
        print(f"F1 Score: {metrics['f1']:.3f}")

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Define output directory
        output_dir = Path("evaluation_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Instantiate the AnomalyEvaluator
        evaluator = AnomalyEvaluator(output_dir=str(output_dir))
                
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Evaluation module loaded successfully")