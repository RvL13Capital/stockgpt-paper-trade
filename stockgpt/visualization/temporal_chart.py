"""
Temporal-Aware Chart with Intelligent Zoom and Volume Adjustment

This module provides interactive charting with temporal-aware zoom that adjusts
volume representation based on the selected timeframe.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import asyncio

from stockgpt.core.entities.stock import Price


@dataclass
class TimeFrame:
    """Represents a temporal timeframe for chart display."""
    name: str
    days: int
    volume_aggregation: str  # 'hourly', 'daily', 'weekly', 'monthly'
    candlestick_interval: str  # '5min', '15min', '1hour', '1day', '1week'

    @property
    def volume_multiplier(self) -> float:
        """Get volume scaling factor based on timeframe."""
        multipliers = {
            'hourly': 24.0,
            'daily': 1.0,
            'weekly': 0.2,
            'monthly': 0.05
        }
        return multipliers.get(self.volume_aggregation, 1.0)


class TemporalChart:
    """
    Interactive chart with temporal-aware zoom and volume adjustment.

    Features:
    - Intelligent zoom that adjusts volume bars based on timeframe
    - Multiple timeframe presets (1D, 5D, 1M, 3M, 6M, 1Y, 5Y)
    - Pattern overlay support for AIv3 consolidation patterns
    - Technical indicator overlays (SMA, Bollinger Bands, etc.)
    - Volume profile analysis
    """

    # Predefined timeframes with appropriate volume aggregation
    TIMEFRAMES = {
        '1D': TimeFrame('1 Day', 1, 'hourly', '5min'),
        '5D': TimeFrame('5 Days', 5, 'hourly', '15min'),
        '1M': TimeFrame('1 Month', 30, 'daily', '1hour'),
        '3M': TimeFrame('3 Months', 90, 'daily', '1day'),
        '6M': TimeFrame('6 Months', 180, 'weekly', '1day'),
        '1Y': TimeFrame('1 Year', 365, 'weekly', '1day'),
        '5Y': TimeFrame('5 Years', 1825, 'monthly', '1week'),
    }

    def __init__(self):
        """Initialize the temporal chart."""
        self.current_timeframe = self.TIMEFRAMES['3M']
        self.fig = None

    def create_chart(self,
                     prices: List[Price],
                     symbol: str,
                     timeframe: str = '3M',
                     patterns: Optional[List[Dict]] = None,
                     indicators: Optional[Dict[str, List[float]]] = None) -> go.Figure:
        """
        Create an interactive chart with temporal-aware features.

        Args:
            prices: List of Price objects
            symbol: Stock symbol
            timeframe: Timeframe key (1D, 5D, 1M, 3M, 6M, 1Y, 5Y)
            patterns: List of detected patterns to overlay
            indicators: Technical indicators to display

        Returns:
            Plotly Figure object
        """
        if not prices:
            raise ValueError("No price data provided")

        self.current_timeframe = self.TIMEFRAMES.get(timeframe, self.TIMEFRAMES['3M'])

        # Convert prices to DataFrame
        df = self._prices_to_dataframe(prices)

        # Aggregate data based on timeframe
        df_aggregated = self._aggregate_by_timeframe(df)

        # Create subplots with shared x-axis
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(
                f'{symbol} - {self.current_timeframe.name}',
                'Volume (Adjusted for Timeframe)',
                'Technical Indicators'
            )
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_aggregated.index,
                open=df_aggregated['Open'],
                high=df_aggregated['High'],
                low=df_aggregated['Low'],
                close=df_aggregated['Close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )

        # Add volume bars with temporal adjustment
        volume_adjusted = df_aggregated['Volume'] * self.current_timeframe.volume_multiplier
        colors = ['#26a69a' if close >= open_ else '#ef5350'
                  for close, open_ in zip(df_aggregated['Close'], df_aggregated['Open'])]

        fig.add_trace(
            go.Bar(
                x=df_aggregated.index,
                y=volume_adjusted,
                name='Volume',
                marker_color=colors,
                opacity=0.5
            ),
            row=2, col=1
        )

        # Add patterns if provided
        if patterns:
            self._add_patterns(fig, patterns, df_aggregated)

        # Add technical indicators
        if indicators:
            self._add_indicators(fig, indicators, df_aggregated)
        else:
            # Add default RSI
            rsi = self._calculate_rsi(df_aggregated['Close'])
            fig.add_trace(
                go.Scatter(
                    x=df_aggregated.index,
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

        # Update layout with temporal-aware features
        fig.update_layout(
            title=f'{symbol} Temporal Chart - {self.current_timeframe.name}',
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
        fig.update_yaxes(title_text=f"Volume ({self._get_volume_unit()})", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)

        # Add timeframe selector buttons
        buttons = self._create_timeframe_buttons()
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

        self.fig = fig
        return fig

    def _prices_to_dataframe(self, prices: List[Price]) -> pd.DataFrame:
        """Convert Price objects to DataFrame."""
        data = []
        for price in prices:
            data.append({
                'Date': pd.to_datetime(price.date),  # Convert to datetime
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

    def _aggregate_by_timeframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate data based on current timeframe settings.

        This is where the temporal magic happens - we adjust the granularity
        of both price and volume data based on the selected timeframe.
        """
        aggregation = self.current_timeframe.volume_aggregation

        if aggregation == 'hourly':
            # For intraday, return as-is (assuming we have minute data)
            return df
        elif aggregation == 'daily':
            # Already daily data
            return df
        elif aggregation == 'weekly':
            # Resample to weekly
            return df.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
        elif aggregation == 'monthly':
            # Resample to monthly
            return df.resample('M').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()

        return df

    def _add_patterns(self, fig: go.Figure, patterns: List[Dict], df: pd.DataFrame):
        """Add AIv3 consolidation patterns to the chart."""
        for pattern in patterns:
            if pattern.get('phase') == 'ACTIVE':
                # Add shaded region for consolidation
                fig.add_shape(
                    type="rect",
                    x0=pattern.get('start_date'),
                    x1=df.index[-1],
                    y0=pattern.get('lower_boundary'),
                    y1=pattern.get('upper_boundary'),
                    fillcolor="LightBlue",
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                    row=1, col=1
                )

                # Add power boundary line
                if pattern.get('power_boundary'):
                    fig.add_hline(
                        y=pattern['power_boundary'],
                        line_dash="dash",
                        line_color="gold",
                        annotation_text="Power Breakout",
                        row=1, col=1
                    )

    def _add_indicators(self, fig: go.Figure, indicators: Dict[str, List[float]],
                       df: pd.DataFrame):
        """Add technical indicators to the chart."""
        # Add to main price chart (row 1)
        if 'sma_20' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=indicators['sma_20'],
                    name='SMA(20)',
                    line=dict(color='orange', width=1)
                ),
                row=1, col=1
            )

        if 'sma_50' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=indicators['sma_50'],
                    name='SMA(50)',
                    line=dict(color='blue', width=1)
                ),
                row=1, col=1
            )

        # Add to indicator panel (row 3)
        if 'rsi' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=indicators['rsi'],
                    name='RSI(14)',
                    line=dict(color='purple', width=2)
                ),
                row=3, col=1
            )

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _get_volume_unit(self) -> str:
        """Get appropriate volume unit based on timeframe."""
        agg = self.current_timeframe.volume_aggregation
        units = {
            'hourly': 'Hourly',
            'daily': 'Daily',
            'weekly': 'Weekly Total',
            'monthly': 'Monthly Total'
        }
        return units.get(agg, 'Daily')

    def _create_timeframe_buttons(self) -> List[Dict]:
        """Create buttons for timeframe selection."""
        buttons = []
        for key, tf in self.TIMEFRAMES.items():
            buttons.append(
                dict(
                    label=key,
                    method="relayout",
                    args=[{"title": f"Chart - {tf.name}"}]
                )
            )
        return buttons

    def save_chart(self, filename: str = "chart.html"):
        """Save the chart as an interactive HTML file."""
        if self.fig:
            self.fig.write_html(filename)
            print(f"Chart saved to {filename}")

    def show_chart(self):
        """Display the chart in browser."""
        if self.fig:
            self.fig.show()


async def create_temporal_chart(symbol: str,
                               timeframe: str = '3M',
                               show_patterns: bool = True) -> go.Figure:
    """
    Create a temporal chart for a symbol with real market data.

    Args:
        symbol: Stock symbol
        timeframe: Timeframe (1D, 5D, 1M, 3M, 6M, 1Y, 5Y)
        show_patterns: Whether to overlay AIv3 patterns

    Returns:
        Plotly Figure object
    """
    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider
    from aiv3.core.consolidation_tracker import ConsolidationTracker

    # Get market data
    provider = EnhancedMarketProvider()

    # Determine days based on timeframe
    tf = TemporalChart.TIMEFRAMES.get(timeframe, TemporalChart.TIMEFRAMES['3M'])
    prices = await provider.get_prices(symbol, days=max(tf.days, 100))

    if not prices:
        raise ValueError(f"No price data found for {symbol}")

    # Detect patterns if requested
    patterns = []
    if show_patterns and len(prices) >= 60:
        tracker = ConsolidationTracker(symbol)
        pattern = tracker.update(prices)
        if pattern and pattern.phase.value == "ACTIVE":
            patterns.append({
                'phase': pattern.phase.value,
                'start_date': prices[-pattern.qualification_days].date if pattern.qualification_days > 0 else prices[0].date,
                'lower_boundary': pattern.lower_boundary,
                'upper_boundary': pattern.upper_boundary,
                'power_boundary': pattern.power_boundary
            })

    # Create chart
    chart = TemporalChart()
    fig = chart.create_chart(
        prices=prices,
        symbol=symbol,
        timeframe=timeframe,
        patterns=patterns
    )

    return fig


if __name__ == "__main__":
    # Example usage
    async def test_chart():
        """Test the temporal chart with real data."""
        print("Creating temporal chart for AAPL...")

        try:
            # Create chart with 3-month view
            fig = await create_temporal_chart("AAPL", timeframe="3M")

            # Save and show
            chart = TemporalChart()
            chart.fig = fig
            chart.save_chart("aapl_temporal_chart.html")
            print("[OK] Chart created successfully!")
            print("Open 'aapl_temporal_chart.html' to view the interactive chart")

            # Test different timeframes
            for tf in ['1D', '5D', '1M', '6M', '1Y']:
                print(f"\nTesting {tf} timeframe...")
                fig = await create_temporal_chart("MSFT", timeframe=tf)
                print(f"[OK] {tf} chart created")

        except Exception as e:
            print(f"[ERROR] {e}")

    # Run test
    asyncio.run(test_chart())