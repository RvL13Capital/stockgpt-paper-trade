"""
XGBoost Model Implementation

Production implementation of the IModel interface using XGBoost.
"""

import joblib
import numpy as np
import xgboost as xgb
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

# Assuming these imports for the example - adjust paths as needed
from stockgpt.core.interfaces.model import IModel

logger = logging.getLogger(__name__)


class XGBoostModel(IModel):
    """Production XGBoost model implementation for pattern classification."""

    # Class values for strategic value calculation
    CLASS_VALUES = {
        0: -2.0,   # K0: <5% gain (Stagnant)
        1: -0.2,   # K1: 5-15% gain (Minimal)
        2: 1.0,    # K2: 15-35% gain (Quality)
        3: 3.0,    # K3: 35-75% gain (Strong)
        4: 10.0,   # K4: >75% gain (Exceptional)
        5: -10.0,  # K5: Breakdown (Failed)
    }

    # Expected feature names in order
    FEATURE_NAMES = [
        'rsi_14',
        'macd',
        'macd_signal',
        'macd_histogram',
        'bbw',
        'bbw_percentile',
        'atr_14',
        'adx',
        'stochastic_k',
        'stochastic_d',
        'williams_r',
        'cci',
        'volume_ratio',
        'price_change_20d',
        'volatility_20d',
        'price_vs_sma20',
        'price_vs_sma50',
        'sma20_vs_sma50',
        'daily_range_ratio',
        'pattern_duration',
    ]

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize XGBoost model.

        Args:
            model_path: Optional path to load model from
        """
        self.model: Optional[xgb.XGBClassifier] = None
        self.feature_names: List[str] = self.FEATURE_NAMES.copy()
        self.model_version: str = "unknown"
        self.training_date: Optional[datetime] = None
        self.model_params: Dict[str, Any] = {}

        if model_path and Path(model_path).exists():
            self.load(model_path)
        else:
            self._initialize_default_model()

    def _initialize_default_model(self) -> None:
        """Initialize model with default parameters."""
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='multi:softprob',
            num_class=6,
            use_label_encoder=False,
            eval_metric='mlogloss',
            random_state=42,
        )
        self.model_version = "default"
        logger.info("Initialized default XGBoost model")

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate prediction from features.

        Args:
            features: Dictionary of feature names to values

        Returns:
            Dictionary containing prediction results

        Raises:
            RuntimeError: If model not loaded
            ValueError: If features are invalid
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load() or train a model first.")

        # Validate features
        is_valid, missing = self.validate_features(features)
        if not is_valid:
            raise ValueError(f"Missing required features: {missing}")

        # Prepare features in correct order
        X = np.array([[features.get(name, 0.0) for name in self.feature_names]])

        # Get prediction probabilities
        try:
            proba = self.model.predict_proba(X)[0]
            prediction = int(self.model.predict(X)[0])
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError(f"Model prediction failed: {e}")

        # Calculate expected value
        expected_value = self._calculate_expected_value(proba)

        # Determine signal strength
        signal_strength = self._determine_signal_strength(proba, expected_value)

        return {
            'prediction': prediction,
            'prediction_class': f'K{prediction}',
            'probabilities': {
                f'K{i}': float(proba[i]) for i in range(len(proba))
            },
            'confidence': float(np.max(proba)),
            'expected_value': expected_value,
            'signal_strength': signal_strength,
            'strategic_value': self.CLASS_VALUES.get(prediction, 0),
            'failure_probability': float(proba[5]) if len(proba) > 5 else 0.0,
        }

    def batch_predict(self, features_list: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Batch prediction for efficiency.

        Args:
            features_list: List of feature dictionaries

        Returns:
            List of prediction dictionaries
        """
        if not self.model:
            raise RuntimeError("Model not loaded")

        # Validate all features first
        for i, features in enumerate(features_list):
            is_valid, missing = self.validate_features(features)
            if not is_valid:
                raise ValueError(f"Features at index {i} missing: {missing}")

        # Prepare feature matrix
        X = np.array([
            [features.get(name, 0.0) for name in self.feature_names]
            for features in features_list
        ])

        # Get batch predictions
        try:
            probas = self.model.predict_proba(X)
            predictions = self.model.predict(X)
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            raise RuntimeError(f"Batch prediction failed: {e}")

        # Build result list
        results = []
        for i, (proba, pred) in enumerate(zip(probas, predictions)):
            expected_value = self._calculate_expected_value(proba)
            signal_strength = self._determine_signal_strength(proba, expected_value)

            results.append({
                'prediction': int(pred),
                'prediction_class': f'K{int(pred)}',
                'probabilities': {
                    f'K{j}': float(proba[j]) for j in range(len(proba))
                },
                'confidence': float(np.max(proba)),
                'expected_value': expected_value,
                'signal_strength': signal_strength,
                'strategic_value': self.CLASS_VALUES.get(int(pred), 0),
                'failure_probability': float(proba[5]) if len(proba) > 5 else 0.0,
            })

        return results

    def _calculate_expected_value(self, probabilities: np.ndarray) -> float:
        """
        Calculate expected value from class probabilities.

        Args:
            probabilities: Array of class probabilities

        Returns:
            Expected value
        """
        values = [self.CLASS_VALUES.get(i, 0) for i in range(len(probabilities))]
        return float(np.dot(probabilities, values))

    def _determine_signal_strength(self, probabilities: np.ndarray, ev: float) -> str:
        """
        Determine signal strength from probabilities and EV.

        Args:
            probabilities: Class probabilities
            ev: Expected value

        Returns:
            Signal strength category
        """
        failure_prob = probabilities[5] if len(probabilities) > 5 else 0.0

        if failure_prob > 0.3:
            return "AVOID"
        elif ev >= 5.0:
            return "STRONG_SIGNAL"
        elif ev >= 3.0:
            return "GOOD_SIGNAL"
        elif ev >= 1.0:
            return "MODERATE_SIGNAL"
        else:
            return "WEAK_SIGNAL"

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importances for model interpretability.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.model:
            return {}

        try:
            importances = self.model.feature_importances_
            return dict(zip(self.feature_names, importances))
        except AttributeError:
            logger.warning("Model doesn't support feature importances")
            return {}

    def get_feature_names(self) -> List[str]:
        """
        Get list of expected feature names in order.

        Returns:
            List of feature names
        """
        return self.feature_names.copy()

    def validate_features(self, features: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate that required features are present.

        Args:
            features: Feature dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_missing_features)
        """
        missing = [name for name in self.feature_names if name not in features]
        return len(missing) == 0, missing

    def load(self, path: str) -> None:
        """
        Load model from disk.

        Args:
            path: Path to model file

        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If model loading fails
        """
        model_path = Path(path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        try:
            model_data = joblib.load(path)

            # Validate loaded data
            if not isinstance(model_data, dict):
                raise ValueError("Invalid model file format")

            self.model = model_data.get('model')
            self.feature_names = model_data.get('feature_names', self.FEATURE_NAMES)
            self.model_version = model_data.get('version', 'unknown')
            self.training_date = model_data.get('training_date')
            self.model_params = model_data.get('params', {})

            logger.info(f"Loaded model version {self.model_version} from {path}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    def save(self, path: str) -> None:
        """
        Save model to disk.

        Args:
            path: Path to save model file

        Raises:
            RuntimeError: If no model to save
        """
        if not self.model:
            raise RuntimeError("No model to save")

        try:
            model_data = {
                'model': self.model,
                'feature_names': self.feature_names,
                'version': self.model_version,
                'training_date': self.training_date or datetime.now(),
                'params': self.model_params,
                'class_values': self.CLASS_VALUES,
            }

            joblib.dump(model_data, path)
            logger.info(f"Saved model to {path}")

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise RuntimeError(f"Model saving failed: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata and information.

        Returns:
            Dictionary with model info
        """
        return {
            'type': 'XGBoostClassifier',
            'version': self.model_version,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'num_features': len(self.feature_names),
            'num_classes': 6,
            'class_labels': ['K0', 'K1', 'K2', 'K3', 'K4', 'K5'],
            'class_values': self.CLASS_VALUES,
            'parameters': self.model_params,
            'is_loaded': self.model is not None,
        }

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Train the model on provided data.

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            params: Model hyperparameters

        Returns:
            Training metrics
        """
        # Set parameters
        if params:
            self.model_params = params
            self.model = xgb.XGBClassifier(**params)
        elif not self.model:
            self._initialize_default_model()

        # Prepare evaluation set
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))

        # Train model
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False,
        )

        # Update metadata
        self.training_date = datetime.now()
        self.model_version = f"trained_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Calculate training metrics
        train_score = self.model.score(X_train, y_train)
        metrics = {'train_accuracy': train_score}

        if X_val is not None and y_val is not None:
            val_score = self.model.score(X_val, y_val)
            metrics['val_accuracy'] = val_score

        logger.info(f"Model trained with metrics: {metrics}")
        return metrics