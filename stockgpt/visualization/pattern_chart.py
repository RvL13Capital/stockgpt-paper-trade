"""
Pattern-Focused Chart with Temporal Context

This module provides enhanced charting specifically for pattern analysis,
showing the full pattern lifecycle with context before and after.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass
import asyncio
import logging

from stockgpt.core.entities.stock import Price

logger = logging.getLogger(__name__)


@dataclass
class PatternPeriod:
    """Represents a detected pattern period with lifecycle stages."""
    symbol: str
    pattern_id: str
    qualification_start: datetime
    active_start: datetime
    breakout_date: Optional[datetime]
    completion_date: Optional[datetime]
    pattern_type: str  # 'consolidation', 'breakout', etc.
    upper_boundary: float
    lower_boundary: float
    power_boundary: float
    outcome: Optional[str]  # 'success', 'failed', 'ongoing'
    gain_percentage: Optional[float]


class PatternChart:
    """
    Enhanced chart for pattern analysis with subtle highlighting and
    temporal context windows.

    Features:
    - Subtle shading for pattern periods (qualification, active, post-breakout)
    - Pattern-focused view: 40 days before + full pattern + 100 days after
    - Navigation between multiple patterns
    - Safety checks for data availability
    """

    # Pattern period colors (subtle, translucent)
    PATTERN_COLORS = {
        'qualification': 'rgba(100, 100, 255, 0.08)',  # Very light blue
        'active': 'rgba(255, 215, 0, 0.12)',           # Very light gold
        'breakout_success': 'rgba(0, 255, 0, 0.08)',   # Very light green
        'breakout_failed': 'rgba(255, 0, 0, 0.08)',    # Very light red
        'ongoing': 'rgba(128, 128, 128, 0.08)'         # Very light gray
    }

    def __init__(self):
        self.current_pattern_index = 0
        self.patterns: List[PatternPeriod] = []
        self.fig = None

    def create_pattern_focused_chart(self,
                                    prices: List[Price],
                                    pattern: PatternPeriod,
                                    context_before: int = 40,
                                    context_after: int = 100,
                                    show_indicators: bool = True) -> go.Figure:
        """
        Create a chart focused on a specific pattern with temporal context.

        Args:
            prices: Full price history
            pattern: The pattern to focus on
            context_before: Days before pattern to show (default 40)
            context_after: Days after breakout to show (default 100)
            show_indicators: Whether to show technical indicators

        Returns:
            Plotly Figure with pattern-focused view
        """
        if not prices:
            raise ValueError("No price data provided")

        # Convert prices to DataFrame
        df = self._prices_to_dataframe(prices)

        # Calculate the viewing window
        window_start, window_end, data_warning = self._calculate_window(
            df, pattern, context_before, context_after
        )

        # Filter data to window
        df_window = df[(df.index >= window_start) & (df.index <= window_end)]

        if len(df_window) == 0:
            raise ValueError(f"No data available for pattern period {window_start} to {window_end}")

        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(
                f'{pattern.symbol} - Pattern Analysis (ID: {pattern.pattern_id})',
                'Volume',
                'Technical Indicators'
            )
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_window.index,
                open=df_window['Open'],
                high=df_window['High'],
                low=df_window['Low'],
                close=df_window['Close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )

        # Add pattern period highlighting
        self._add_pattern_highlighting(fig, pattern, df_window)

        # Add boundary lines
        self._add_boundary_lines(fig, pattern, df_window)

        # Add volume bars
        colors = ['#26a69a' if close >= open_ else '#ef5350'
                  for close, open_ in zip(df_window['Close'], df_window['Open'])]

        fig.add_trace(
            go.Bar(
                x=df_window.index,
                y=df_window['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )

        # Add technical indicators if requested
        if show_indicators:
            self._add_technical_indicators(fig, df_window)

        # Add annotations for key events
        self._add_pattern_annotations(fig, pattern, df_window)

        # Update layout
        title = f'{pattern.symbol} Pattern Analysis - {pattern.pattern_type.title()}'
        if data_warning:
            title += f' ({data_warning})'

        fig.update_layout(
            title=title,
            xaxis_rangeslider_visible=False,
            height=800,
            template='plotly_dark',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # Update axes
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)

        self.fig = fig
        return fig

    def create_multi_pattern_chart(self,
                                  prices: List[Price],
                                  patterns: List[PatternPeriod],
                                  show_all: bool = False) -> go.Figure:
        """
        Create a chart showing multiple patterns with navigation.

        Args:
            prices: Full price history
            patterns: List of patterns to display
            show_all: If True, show all patterns on one chart

        Returns:
            Plotly Figure with pattern visualization
        """
        if not patterns:
            raise ValueError("No patterns provided")

        self.patterns = patterns
        df = self._prices_to_dataframe(prices)

        if show_all:
            # Show all patterns on single chart
            fig = self._create_overview_chart(df, patterns)
        else:
            # Show first pattern with navigation buttons
            fig = self.create_pattern_focused_chart(
                prices, patterns[0]
            )
            self._add_navigation_buttons(fig)

        return fig

    def _create_overview_chart(self,
                               df: pd.DataFrame,
                               patterns: List[PatternPeriod]) -> go.Figure:
        """Create overview chart showing all patterns with subtle highlighting."""

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(
                'Price with Pattern Periods',
                'Volume'
            )
        )

        # Add candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )

        # Add subtle highlighting for each pattern
        for pattern in patterns:
            self._add_pattern_highlighting(fig, pattern, df, subtle=True)

        # Add volume
        colors = ['#26a69a' if close >= open_ else '#ef5350'
                  for close, open_ in zip(df['Close'], df['Open'])]

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )

        # Add pattern markers
        for i, pattern in enumerate(patterns):
            if pd.Timestamp(pattern.active_start) in df.index:
                fig.add_annotation(
                    x=pattern.active_start,
                    y=df.loc[pd.Timestamp(pattern.active_start), 'High'],
                    text=f"P{i+1}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor="gold",
                    ax=0,
                    ay=-30,
                    row=1, col=1
                )

        fig.update_layout(
            title=f'Pattern Overview - {len(patterns)} Patterns Detected',
            xaxis_rangeslider_visible=False,
            height=700,
            template='plotly_dark',
            hovermode='x unified'
        )

        return fig

    def _calculate_window(self,
                         df: pd.DataFrame,
                         pattern: PatternPeriod,
                         context_before: int,
                         context_after: int) -> Tuple[datetime, datetime, Optional[str]]:
        """
        Calculate the viewing window for a pattern with safety checks.

        Returns:
            Tuple of (start_date, end_date, warning_message)
        """
        warning = None

        # Calculate ideal window
        ideal_start = pattern.qualification_start - timedelta(days=context_before)

        if pattern.breakout_date:
            ideal_end = pattern.breakout_date + timedelta(days=context_after)
        else:
            # Pattern is ongoing or failed without breakout
            ideal_end = pattern.completion_date or datetime.now()
            warning = "Pattern ongoing or incomplete"

        # Check data availability
        actual_start = max(ideal_start, df.index[0])
        actual_end = min(ideal_end, df.index[-1])

        # Generate warnings if we don't have full context
        if actual_start > ideal_start:
            days_missing = (actual_start - ideal_start).days
            warning = f"Only {context_before - days_missing} days before pattern available"

        if pattern.breakout_date and actual_end < ideal_end:
            days_missing = (ideal_end - actual_end).days
            days_available = (actual_end - pattern.breakout_date).days
            if warning:
                warning += f", only {days_available} days after breakout available"
            else:
                warning = f"Only {days_available} days after breakout available (requested {context_after})"

        return actual_start, actual_end, warning

    def _add_pattern_highlighting(self,
                                 fig: go.Figure,
                                 pattern: PatternPeriod,
                                 df: pd.DataFrame,
                                 subtle: bool = True):
        """Add subtle shading for pattern periods."""

        # Qualification period
        qual_start = pd.Timestamp(pattern.qualification_start)
        active_start = pd.Timestamp(pattern.active_start)

        if qual_start in df.index:
            fig.add_vrect(
                x0=pattern.qualification_start,
                x1=pattern.active_start,
                fillcolor=self.PATTERN_COLORS['qualification'],
                opacity=0.5 if not subtle else 0.3,
                layer="below",
                line_width=0,
                annotation_text="Qualification" if not subtle else None,
                annotation_position="top left",
                row=1, col=1
            )

        # Active period
        if active_start in df.index:
            active_end = pd.Timestamp(pattern.breakout_date) if pattern.breakout_date else (pd.Timestamp(pattern.completion_date) if pattern.completion_date else df.index[-1])

            if pattern.outcome == 'success':
                color = self.PATTERN_COLORS['active']
            elif pattern.outcome == 'failed':
                color = self.PATTERN_COLORS['breakout_failed']
            else:
                color = self.PATTERN_COLORS['ongoing']

            fig.add_vrect(
                x0=pattern.active_start,
                x1=active_end,
                fillcolor=color,
                opacity=0.5 if not subtle else 0.3,
                layer="below",
                line_width=0,
                annotation_text="Active" if not subtle else None,
                annotation_position="top left",
                row=1, col=1
            )

        # Post-breakout period (if applicable)
        if pattern.breakout_date:
            breakout_ts = pd.Timestamp(pattern.breakout_date)
            if breakout_ts in df.index:
                post_end = min(
                    pd.Timestamp(pattern.breakout_date + timedelta(days=100)),
                    df.index[-1]
                )

            outcome_color = (self.PATTERN_COLORS['breakout_success']
                           if pattern.outcome == 'success'
                           else self.PATTERN_COLORS['breakout_failed'])

            fig.add_vrect(
                x0=pattern.breakout_date,
                x1=post_end,
                fillcolor=outcome_color,
                opacity=0.3 if not subtle else 0.2,
                layer="below",
                line_width=0,
                annotation_text="Post-Breakout" if not subtle else None,
                annotation_position="top left",
                row=1, col=1
            )

    def _add_boundary_lines(self,
                           fig: go.Figure,
                           pattern: PatternPeriod,
                           df: pd.DataFrame):
        """Add horizontal lines for pattern boundaries."""

        # Upper boundary
        fig.add_hline(
            y=pattern.upper_boundary,
            line_dash="dash",
            line_color="red",
            line_width=1,
            opacity=0.6,
            annotation_text=f"Upper: ${pattern.upper_boundary:.2f}",
            annotation_position="right",
            row=1, col=1
        )

        # Lower boundary
        fig.add_hline(
            y=pattern.lower_boundary,
            line_dash="dash",
            line_color="green",
            line_width=1,
            opacity=0.6,
            annotation_text=f"Lower: ${pattern.lower_boundary:.2f}",
            annotation_position="right",
            row=1, col=1
        )

        # Power boundary (breakout target)
        fig.add_hline(
            y=pattern.power_boundary,
            line_dash="dot",
            line_color="gold",
            line_width=2,
            opacity=0.8,
            annotation_text=f"Power Target: ${pattern.power_boundary:.2f}",
            annotation_position="right",
            row=1, col=1
        )

    def _add_pattern_annotations(self,
                                fig: go.Figure,
                                pattern: PatternPeriod,
                                df: pd.DataFrame):
        """Add annotations for key pattern events."""

        # Mark pattern start
        if pd.Timestamp(pattern.qualification_start) in df.index:
            fig.add_annotation(
                x=pattern.qualification_start,
                y=df.loc[pd.Timestamp(pattern.qualification_start), 'Low'],
                text="Pattern Start",
                showarrow=True,
                arrowhead=2,
                arrowcolor="blue",
                ax=0,
                ay=40,
                row=1, col=1
            )

        # Mark activation
        if pd.Timestamp(pattern.active_start) in df.index:
            fig.add_annotation(
                x=pattern.active_start,
                y=df.loc[pd.Timestamp(pattern.active_start), 'Low'],
                text="Activated",
                showarrow=True,
                arrowhead=2,
                arrowcolor="gold",
                ax=0,
                ay=40,
                row=1, col=1
            )

        # Mark breakout if occurred
        if pattern.breakout_date and pd.Timestamp(pattern.breakout_date) in df.index:
            breakout_text = f"Breakout ({pattern.gain_percentage:.1f}%)" if pattern.gain_percentage else "Breakout"
            fig.add_annotation(
                x=pattern.breakout_date,
                y=df.loc[pd.Timestamp(pattern.breakout_date), 'High'],
                text=breakout_text,
                showarrow=True,
                arrowhead=2,
                arrowcolor="green" if pattern.outcome == 'success' else "red",
                ax=0,
                ay=-40,
                row=1, col=1
            )

    def _add_technical_indicators(self,
                                 fig: go.Figure,
                                 df: pd.DataFrame):
        """Add technical indicators to the chart."""

        # Calculate RSI
        rsi = self._calculate_rsi(df['Close'])

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=rsi,
                name='RSI(14)',
                line=dict(color='purple', width=2)
            ),
            row=3, col=1
        )

        # Add RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red",
                     opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green",
                     opacity=0.5, row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray",
                     opacity=0.3, row=3, col=1)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _prices_to_dataframe(self, prices: List[Price]) -> pd.DataFrame:
        """Convert Price objects to DataFrame with DatetimeIndex."""
        data = []
        for price in prices:
            data.append({
                'Date': pd.to_datetime(price.date),
                'Open': price.open,
                'High': price.high,
                'Low': price.low,
                'Close': price.close,
                'Volume': price.volume
            })
        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        return df

    def _add_navigation_buttons(self, fig: go.Figure):
        """Add navigation buttons to jump between patterns."""

        if len(self.patterns) <= 1:
            return

        buttons = []
        for i, pattern in enumerate(self.patterns):
            label = f"Pattern {i+1}"
            if pattern.outcome:
                label += f" ({pattern.outcome})"

            buttons.append(
                dict(
                    label=label,
                    method="relayout",
                    args=[{"title": f"Pattern {i+1} - {pattern.pattern_type}"}]
                )
            )

        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.01,
                    xanchor="left",
                    y=1.15,
                    yanchor="top",
                    buttons=buttons
                )
            ]
        )


async def analyze_historical_patterns(symbol: str,
                                     lookback_days: int = 365) -> List[PatternPeriod]:
    """
    Analyze historical data to find all patterns for a symbol.

    Args:
        symbol: Stock symbol
        lookback_days: Days of history to analyze

    Returns:
        List of detected patterns with full lifecycle data
    """
    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider
    from aiv3.core.consolidation_tracker import ConsolidationTracker

    provider = EnhancedMarketProvider()

    # Get historical data
    prices = await provider.get_prices(symbol, days=lookback_days)

    if not prices or len(prices) < 100:
        logger.warning(f"Insufficient data for pattern analysis of {symbol}")
        return []

    patterns = []
    tracker = ConsolidationTracker(symbol)

    # Simulate day-by-day analysis to find historical patterns
    for i in range(100, len(prices)):
        window = prices[:i+1]  # Only use data up to this point (no look-ahead)
        pattern = tracker.update(window)

        if pattern and pattern.phase.value == "ACTIVE":
            # Track this pattern
            pattern_period = PatternPeriod(
                symbol=symbol,
                pattern_id=f"{symbol}_{i}",
                qualification_start=pd.Timestamp(window[-pattern.qualification_days].date) if pattern.qualification_days > 0 else pd.Timestamp(window[0].date),
                active_start=pd.Timestamp(window[-1].date),
                breakout_date=None,
                completion_date=None,
                pattern_type='consolidation',
                upper_boundary=pattern.upper_boundary,
                lower_boundary=pattern.lower_boundary,
                power_boundary=pattern.power_boundary,
                outcome='ongoing',
                gain_percentage=None
            )

            # Check if pattern broke out in subsequent days
            for j in range(i+1, min(i+101, len(prices))):  # Check next 100 days
                if prices[j].high > pattern.power_boundary:
                    pattern_period.breakout_date = pd.Timestamp(prices[j].date)

                    # Calculate gain percentage
                    breakout_price = pattern.power_boundary
                    max_price = max(p.high for p in prices[j:min(j+100, len(prices))])
                    pattern_period.gain_percentage = ((max_price - breakout_price) / breakout_price) * 100

                    if pattern_period.gain_percentage > 10:
                        pattern_period.outcome = 'success'
                    else:
                        pattern_period.outcome = 'failed'

                    pattern_period.completion_date = pd.Timestamp(prices[min(j+100, len(prices)-1)].date)
                    break
                elif prices[j].low < pattern.lower_boundary:
                    # Pattern failed (broke down)
                    pattern_period.outcome = 'failed'
                    pattern_period.completion_date = pd.Timestamp(prices[j].date)
                    break

            patterns.append(pattern_period)

    return patterns


async def create_pattern_analysis_chart(symbol: str,
                                       pattern_id: Optional[str] = None,
                                       show_all_patterns: bool = False) -> go.Figure:
    """
    Create a comprehensive pattern analysis chart for a symbol.

    Args:
        symbol: Stock symbol to analyze
        pattern_id: Specific pattern ID to focus on
        show_all_patterns: If True, show all patterns in overview

    Returns:
        Interactive Plotly chart with pattern analysis
    """
    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

    provider = EnhancedMarketProvider()

    # Get price data
    prices = await provider.get_prices(symbol, days=500)

    if not prices:
        raise ValueError(f"No price data found for {symbol}")

    # Analyze patterns
    patterns = await analyze_historical_patterns(symbol, lookback_days=365)

    if not patterns:
        logger.info(f"No patterns found for {symbol}")
        # Create regular chart
        from stockgpt.visualization.temporal_chart import TemporalChart
        chart = TemporalChart()
        return chart.create_chart(prices, symbol, timeframe='3M')

    # Create pattern chart
    pattern_chart = PatternChart()

    if pattern_id:
        # Find specific pattern
        pattern = next((p for p in patterns if p.pattern_id == pattern_id), None)
        if pattern:
            return pattern_chart.create_pattern_focused_chart(
                prices, pattern, context_before=40, context_after=100
            )

    if show_all_patterns or len(patterns) > 1:
        return pattern_chart.create_multi_pattern_chart(
            prices, patterns, show_all=show_all_patterns
        )
    else:
        # Single pattern found
        return pattern_chart.create_pattern_focused_chart(
            prices, patterns[0], context_before=40, context_after=100
        )


if __name__ == "__main__":
    # Example usage
    async def test_pattern_chart():
        """Test pattern-focused charting."""

        print("Analyzing patterns for AAPL...")

        try:
            # Create pattern analysis chart
            fig = await create_pattern_analysis_chart(
                "AAPL",
                show_all_patterns=True
            )

            # Save chart
            fig.write_html("aapl_pattern_analysis.html")
            print("[OK] Pattern analysis chart created!")
            print("Open 'aapl_pattern_analysis.html' to view")

            # Test individual pattern view
            patterns = await analyze_historical_patterns("AAPL")
            if patterns:
                print(f"\nFound {len(patterns)} patterns:")
                for i, p in enumerate(patterns[:5]):  # Show first 5
                    print(f"  {i+1}. {p.pattern_id}: {p.outcome} "
                          f"({p.gain_percentage:.1f}% gain)" if p.gain_percentage else "")

                # Create focused chart for first pattern
                if patterns:
                    fig2 = await create_pattern_analysis_chart(
                        "AAPL",
                        pattern_id=patterns[0].pattern_id
                    )
                    fig2.write_html("aapl_pattern_focused.html")
                    print("\n[OK] Pattern-focused chart created!")
                    print("Open 'aapl_pattern_focused.html' to view")

        except Exception as e:
            print(f"[ERROR] {e}")

    # Run test
    asyncio.run(test_pattern_chart())