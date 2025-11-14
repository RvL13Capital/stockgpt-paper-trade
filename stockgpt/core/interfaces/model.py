"""
Machine Learning Model Interface

This protocol defines the contract for all ML model implementations,
whether XGBoost, neural networks, or mock models for testing.
"""

from typing import Protocol, Dict, Any, List, Optional, Tuple
import numpy as np
from pathlib import Path


class IModel(Protocol):
    """Machine learning model interface for pattern prediction."""

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate prediction from feature dictionary.

        Args:
            features: Dictionary of feature names to values

        Returns:
            Dictionary containing:
                - prediction: Predicted class (K0-K5)
                - probabilities: Dict of class probabilities
                - confidence: Overall prediction confidence (0-1)
                - expected_value: Calculated expected value
        """
        ...

    def batch_predict(self, features_list: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Batch prediction for efficiency when processing multiple samples.

        Args:
            features_list: List of feature dictionaries

        Returns:
            List of prediction dictionaries
        """
        ...

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importances for model interpretability.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        ...

    def get_feature_names(self) -> List[str]:
        """
        Get list of expected feature names in order.

        Returns:
            List of feature names
        """
        ...

    def validate_features(self, features: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate that required features are present.

        Args:
            features: Feature dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_missing_features)
        """
        ...

    def load(self, path: str) -> None:
        """
        Load model from disk.

        Args:
            path: Path to model file

        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If model loading fails
        """
        ...

    def save(self, path: str) -> None:
        """
        Save model to disk.

        Args:
            path: Path to save model file

        Raises:
            RuntimeError: If no model to save
        """
        ...

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata and information.

        Returns:
            Dictionary with model info (version, type, training_date, etc.)
        """
        ...