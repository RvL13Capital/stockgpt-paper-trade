"""
Model Training Pipeline

Trains XGBoost model on real historical patterns and their actual outcomes.
No mock data - everything is based on real market performance.
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Optional
import joblib
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
import optuna

from aiv3.core.consolidation_tracker import ConsolidationTracker
from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
from stockgpt.infrastructure.ml.xgboost_model import XGBoostModel
from stockgpt.core.entities.pattern import Pattern, PatternOutcome, OutcomeClass

logger = logging.getLogger(__name__)


class ModelTrainingPipeline:
    """
    End-to-end pipeline for training pattern detection models on real data.

    Steps:
    1. Collect historical price data (4+ years)
    2. Detect patterns in historical data
    3. Evaluate pattern outcomes using future prices
    4. Train XGBoost on pattern features and outcomes
    5. Validate on out-of-sample data
    """

    def __init__(
        self,
        data_provider: MarketDataProvider,
        model_path: str = "./models/aiv3_pattern_model.pkl",
        min_training_years: int = 2,
        evaluation_window: int = 100,
    ):
        """
        Initialize training pipeline.

        Args:
            data_provider: Real market data provider
            model_path: Path to save trained model
            min_training_years: Minimum years of data for training
            evaluation_window: Days to evaluate pattern outcomes
        """
        self.data_provider = data_provider
        self.model_path = Path(model_path)
        self.min_training_years = min_training_years
        self.evaluation_window = evaluation_window

        # Ensure model directory exists
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        # Training data storage
        self.patterns: List[Pattern] = []
        self.pattern_outcomes: List[PatternOutcome] = []
        self.pattern_features: List[Dict[str, float]] = []

    async def train_model(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        validation_split: float = 0.2,
        optimize_hyperparameters: bool = True,
    ) -> Dict[str, Any]:
        """
        Train model on real historical patterns.

        Args:
            symbols: List of stock symbols to train on
            start_date: Start of training period
            end_date: End of training period
            validation_split: Fraction of data for validation
            optimize_hyperparameters: Whether to run hyperparameter optimization

        Returns:
            Training results and metrics
        """
        logger.info(f"Starting model training on {len(symbols)} symbols from {start_date} to {end_date}")

        # Step 1: Collect patterns from historical data
        await self._collect_historical_patterns(symbols, start_date, end_date)

        if len(self.patterns) < 100:
            raise ValueError(f"Insufficient patterns for training: {len(self.patterns)}. Need at least 100.")

        logger.info(f"Collected {len(self.patterns)} patterns with outcomes")

        # Step 2: Prepare training data
        X, y = self._prepare_training_data()

        # Step 3: Split data temporally (not randomly!) for proper validation
        split_index = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_index], X[split_index:]
        y_train, y_val = y[:split_index], y[split_index:]

        logger.info(f"Training set: {len(X_train)} samples, Validation set: {len(X_val)} samples")

        # Step 4: Optimize hyperparameters if requested
        if optimize_hyperparameters:
            best_params = await self._optimize_hyperparameters(X_train, y_train, X_val, y_val)
        else:
            best_params = self._get_default_params()

        # Step 5: Train final model
        model = XGBoostModel()
        metrics = model.train(X_train, y_train, X_val, y_val, best_params)

        # Step 6: Evaluate on validation set
        val_predictions = model.model.predict(X_val)
        val_report = classification_report(
            y_val, val_predictions,
            target_names=[f'K{i}' for i in range(6)],
            output_dict=True
        )

        # Step 7: Calculate expected value correlation
        ev_correlation = self._calculate_ev_correlation(model, X_val, y_val)

        # Step 8: Save trained model
        model.save(str(self.model_path))
        logger.info(f"Model saved to {self.model_path}")

        # Prepare results
        results = {
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'total_patterns': len(self.patterns),
            'symbols_trained': len(symbols),
            'date_range': f"{start_date} to {end_date}",
            'train_accuracy': metrics['train_accuracy'],
            'val_accuracy': metrics.get('val_accuracy', 0),
            'ev_correlation': ev_correlation,
            'classification_report': val_report,
            'hyperparameters': best_params,
            'class_distribution': self._get_class_distribution(y),
            'model_path': str(self.model_path),
        }

        return results

    async def _collect_historical_patterns(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> None:
        """
        Collect patterns from historical data.

        This scans through historical prices to find consolidation patterns
        and evaluates their actual outcomes using future price data.
        """
        self.patterns = []
        self.pattern_outcomes = []
        self.pattern_features = []

        for symbol in symbols:
            logger.info(f"Scanning {symbol} for patterns...")

            # Get all historical data including evaluation window
            extended_end = end_date + timedelta(days=self.evaluation_window + 30)
            prices = await self.data_provider.get_prices(
                symbol,
                start_date=start_date,
                end_date=extended_end
            )

            if len(prices) < 200:
                logger.warning(f"Insufficient data for {symbol}: {len(prices)} days")
                continue

            # Initialize tracker
            tracker = ConsolidationTracker(
                symbol=symbol,
                evaluation_window=self.evaluation_window
            )

            # Scan through prices day by day (simulating real-time detection)
            for i in range(60, len(prices) - self.evaluation_window):
                # Get data up to current day (no look-ahead!)
                current_prices = prices[:i+1]

                # Update tracker
                pattern = tracker.update(current_prices)

                # Check if pattern just completed
                if (pattern and
                    pattern.phase in [PatternPhase.COMPLETED, PatternPhase.FAILED] and
                    pattern not in self.patterns):

                    # Get future prices for outcome evaluation
                    future_prices = prices[i+1:i+1+self.evaluation_window]

                    if len(future_prices) >= 20:  # Need sufficient future data
                        # Evaluate actual outcome
                        outcome = tracker.evaluate_pattern_outcome(pattern, future_prices)

                        if outcome:
                            # Extract features
                            features = tracker.get_pattern_features(pattern)

                            # Store for training
                            self.patterns.append(pattern)
                            self.pattern_outcomes.append(outcome)
                            self.pattern_features.append(features)

            # Log statistics for this symbol
            stats = tracker.get_statistics()
            logger.info(
                f"{symbol}: Found {stats.get('total_patterns', 0)} patterns, "
                f"Success rate: {stats.get('success_rate', 0):.2%}"
            )

    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and labels for training.

        Returns:
            X: Feature matrix
            y: Labels (outcome classes)
        """
        # Create DataFrame from features
        df = pd.DataFrame(self.pattern_features)

        # Fill missing values with median
        df = df.fillna(df.median())

        # Add additional engineered features
        df['range_to_duration_ratio'] = df['range_percentage'] / (df['pattern_duration'] + 1)
        df['volatility_to_bbw_ratio'] = df['avg_volatility'] / (df['avg_bbw'] + 0.01)
        df['volume_consistency'] = df['avg_volume_ratio'] / (df['volume_slope'].abs() + 0.01)

        # Ensure all expected features are present
        expected_features = XGBoostModel.FEATURE_NAMES
        for feature in expected_features:
            if feature not in df.columns:
                df[feature] = 0.0  # Add with default value

        # Select features in correct order
        X = df[expected_features].values

        # Create labels from outcomes
        y = np.array([outcome.outcome_class.value[1] for outcome in self.pattern_outcomes])  # K0->0, K1->1, etc.

        return X.astype(np.float32), y.astype(np.int32)

    async def _optimize_hyperparameters(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        n_trials: int = 50,
    ) -> Dict[str, Any]:
        """
        Optimize hyperparameters using Optuna.

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            n_trials: Number of optimization trials

        Returns:
            Best hyperparameters
        """
        logger.info(f"Starting hyperparameter optimization with {n_trials} trials...")

        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 7),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
                'gamma': trial.suggest_float('gamma', 0, 0.5),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 1.0),
                'objective': 'multi:softprob',
                'num_class': 6,
                'use_label_encoder': False,
                'eval_metric': 'mlogloss',
                'random_state': 42,
            }

            # Train model with current parameters
            model = xgb.XGBClassifier(**params)
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
                early_stopping_rounds=20,
            )

            # Calculate expected value score (our custom metric)
            val_proba = model.predict_proba(X_val)
            ev_score = self._calculate_ev_score(val_proba, y_val)

            return ev_score

        # Run optimization
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

        best_params = study.best_params
        best_params.update({
            'objective': 'multi:softprob',
            'num_class': 6,
            'use_label_encoder': False,
            'eval_metric': 'mlogloss',
            'random_state': 42,
        })

        logger.info(f"Best EV score: {study.best_value:.4f}")
        logger.info(f"Best parameters: {best_params}")

        return best_params

    def _get_default_params(self) -> Dict[str, Any]:
        """Get default XGBoost parameters."""
        return {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'min_child_weight': 3,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0.1,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'objective': 'multi:softprob',
            'num_class': 6,
            'use_label_encoder': False,
            'eval_metric': 'mlogloss',
            'random_state': 42,
        }

    def _calculate_ev_score(self, probabilities: np.ndarray, true_labels: np.ndarray) -> float:
        """
        Calculate expected value score for optimization.

        This is our custom metric that considers the strategic value
        of correctly predicting high-value patterns (K4) vs avoiding failures (K5).
        """
        class_values = XGBoostModel.CLASS_VALUES
        score = 0.0

        for i, true_label in enumerate(true_labels):
            # Calculate expected value from predicted probabilities
            ev = sum(prob * class_values[j] for j, prob in enumerate(probabilities[i]))

            # Reward correct high-value predictions more
            if true_label == 4 and probabilities[i][4] > 0.3:  # K4 correctly predicted
                score += 10.0
            elif true_label == 5 and probabilities[i][5] > 0.3:  # K5 correctly avoided
                score += 5.0
            elif ev > 3.0 and true_label in [3, 4]:  # Good signal on good outcome
                score += 3.0
            elif ev < 0 and true_label == 5:  # Correctly avoided failure
                score += 2.0
            else:
                score += max(0, ev)  # Regular EV contribution

        return score / len(true_labels)

    def _calculate_ev_correlation(
        self,
        model: XGBoostModel,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> float:
        """
        Calculate correlation between predicted and actual expected values.

        This measures how well the model's expected value predictions
        align with actual outcomes.
        """
        predictions = model.batch_predict([
            {model.feature_names[j]: X_val[i, j] for j in range(X_val.shape[1])}
            for i in range(len(X_val))
        ])

        predicted_evs = [p['expected_value'] for p in predictions]

        # Calculate actual values based on true labels
        class_values = XGBoostModel.CLASS_VALUES
        actual_values = [class_values[int(label)] for label in y_val]

        # Calculate correlation
        correlation = np.corrcoef(predicted_evs, actual_values)[0, 1]

        return float(correlation)

    def _get_class_distribution(self, labels: np.ndarray) -> Dict[str, int]:
        """Get distribution of outcome classes."""
        unique, counts = np.unique(labels, return_counts=True)
        return {
            f'K{int(label)}': int(count)
            for label, count in zip(unique, counts)
        }

    async def backtest_model(
        self,
        model_path: str,
        symbols: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """
        Backtest trained model on new data.

        Args:
            model_path: Path to trained model
            symbols: Symbols to test on
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            Backtest results
        """
        logger.info(f"Starting backtest from {start_date} to {end_date}")

        # Load model
        model = XGBoostModel(model_path)

        # Collect patterns from test period
        await self._collect_historical_patterns(symbols, start_date, end_date)

        if not self.patterns:
            return {'error': 'No patterns found in test period'}

        # Prepare test data
        X_test, y_test = self._prepare_training_data()

        # Generate predictions
        predictions = model.batch_predict([
            {model.feature_names[j]: X_test[i, j] for j in range(X_test.shape[1])}
            for i in range(len(X_test))
        ])

        # Analyze results
        strong_signals = [p for p in predictions if p['signal_strength'] == 'STRONG_SIGNAL']
        good_signals = [p for p in predictions if p['signal_strength'] == 'GOOD_SIGNAL']

        # Calculate performance metrics
        results = {
            'total_patterns': len(self.patterns),
            'strong_signals': len(strong_signals),
            'good_signals': len(good_signals),
            'signal_rate': (len(strong_signals) + len(good_signals)) / len(predictions),
            'ev_correlation': self._calculate_ev_correlation(model, X_test, y_test),
            'class_distribution': self._get_class_distribution(y_test),
        }

        # Calculate accuracy for each signal strength
        for strength in ['STRONG_SIGNAL', 'GOOD_SIGNAL', 'MODERATE_SIGNAL']:
            signal_indices = [
                i for i, p in enumerate(predictions)
                if p['signal_strength'] == strength
            ]

            if signal_indices:
                actual_outcomes = y_test[signal_indices]
                successful = sum(1 for o in actual_outcomes if o in [3, 4])  # K3, K4
                results[f'{strength.lower()}_success_rate'] = successful / len(signal_indices)

        return results