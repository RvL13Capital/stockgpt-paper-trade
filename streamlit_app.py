"""
StockGPT Web Application - Free Deployment

This Streamlit app provides a web interface for the StockGPT system.
Deploy for free on Streamlit Community Cloud, Render, or Railway.
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from typing import List, Optional

# Configure page
st.set_page_config(
    page_title="StockGPT Pattern Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set API keys from Streamlit secrets, environment variables, or fallback
try:
    # Try Streamlit secrets first (for Streamlit Cloud)
    if 'TWELVEDATA_API_KEY' in st.secrets:
        os.environ['TWELVEDATA_API_KEY'] = st.secrets['TWELVEDATA_API_KEY']
        os.environ['ALPHA_VANTAGE_API_KEY'] = st.secrets['ALPHA_VANTAGE_API_KEY']
        os.environ['FMP_API_KEY'] = st.secrets['FMP_API_KEY']
        os.environ['FINNHUB_API_KEY'] = st.secrets['FINNHUB_API_KEY']
except:
    # If secrets.toml doesn't exist, environment variables from Render/Railway/Heroku are already available
    # Only set fallback if environment variables are not set
    if 'TWELVEDATA_API_KEY' not in os.environ:
        os.environ['TWELVEDATA_API_KEY'] = '5361b6392f4941d99f08d14d22551cb2'
        os.environ['ALPHA_VANTAGE_API_KEY'] = 'FPG7DCR33BFK2HDP'
        os.environ['FMP_API_KEY'] = 'smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm'
        os.environ['FINNHUB_API_KEY'] = 'd2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80'


# Cache data fetching to minimize API calls
@st.cache_data(ttl=900)  # Cache for 15 minutes
def fetch_market_data(symbol: str, days: int = 100):
    """Fetch market data with caching."""
    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

    async def get_data():
        provider = EnhancedMarketProvider()
        prices = await provider.get_prices(symbol, days=days)
        return prices

    return asyncio.run(get_data())


@st.cache_data(ttl=900)
def detect_patterns(symbol: str):
    """Detect patterns in stock data."""
    from aiv3.core.consolidation_tracker import ConsolidationTracker

    prices = fetch_market_data(symbol, days=200)
    if not prices or len(prices) < 60:
        return None, prices

    tracker = ConsolidationTracker(symbol)
    pattern = tracker.update(prices)
    return pattern, prices


def create_price_chart(prices, symbol: str, pattern=None):
    """Create interactive price chart with pattern overlay."""
    if not prices:
        return None

    # Convert to DataFrame
    df = pd.DataFrame([{
        'Date': pd.to_datetime(p.date),
        'Open': p.open,
        'High': p.high,
        'Low': p.low,
        'Close': p.close,
        'Volume': p.volume
    } for p in prices])
    df.set_index('Date', inplace=True)

    # Create figure with subplots
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{symbol} Price', 'Volume')
    )

    # Add candlestick chart
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

    # Add pattern overlay if detected
    if pattern and hasattr(pattern, 'phase') and pattern.phase.value == "ACTIVE":
        # Add shaded region for consolidation
        fig.add_shape(
            type="rect",
            x0=df.index[-pattern.qualification_days] if pattern.qualification_days > 0 else df.index[0],
            x1=df.index[-1],
            y0=pattern.lower_boundary,
            y1=pattern.upper_boundary,
            fillcolor="rgba(255, 215, 0, 0.1)",
            line=dict(width=0),
            row=1, col=1
        )

        # Add boundary lines
        fig.add_hline(
            y=pattern.upper_boundary,
            line_dash="dash",
            line_color="red",
            opacity=0.6,
            annotation_text=f"Upper: ${pattern.upper_boundary:.2f}",
            row=1, col=1
        )

        fig.add_hline(
            y=pattern.lower_boundary,
            line_dash="dash",
            line_color="green",
            opacity=0.6,
            annotation_text=f"Lower: ${pattern.lower_boundary:.2f}",
            row=1, col=1
        )

        fig.add_hline(
            y=pattern.power_boundary,
            line_dash="dot",
            line_color="gold",
            opacity=0.8,
            annotation_text=f"Target: ${pattern.power_boundary:.2f}",
            row=1, col=1
        )

    # Add volume bars
    colors = ['#26a69a' if c >= o else '#ef5350'
              for c, o in zip(df['Close'], df['Open'])]

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

    # Update layout
    fig.update_layout(
        height=600,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        template='plotly_dark' if st.session_state.get('dark_mode', False) else 'plotly_white',
        margin=dict(l=0, r=0, t=30, b=0)
    )

    return fig


def create_signal_card(signal):
    """Create a card display for a signal."""
    color_map = {
        'STRONG_BUY': '#00ff00',
        'BUY': '#90ee90',
        'HOLD': '#ffff00',
        'SELL': '#ffa500',
        'STRONG_SELL': '#ff0000'
    }

    color = color_map.get(signal.get('action', 'HOLD'), '#808080')

    return f"""
    <div style="border: 2px solid {color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
        <h4 style="color: {color}; margin: 0;">{signal.get('symbol')} - {signal.get('action')}</h4>
        <p><b>Price:</b> ${signal.get('price', 0):.2f}</p>
        <p><b>RSI:</b> {signal.get('rsi', 0):.1f}</p>
        <p><b>Reason:</b> {signal.get('reason', 'N/A')}</p>
    </div>
    """


# Main app
def main():
    st.title("📊 StockGPT Pattern Analyzer")
    st.markdown("AI-powered consolidation pattern detection and breakout prediction")

    # Sidebar
    with st.sidebar:
        st.header("Configuration")

        # Input section
        symbol = st.text_input("Stock Symbol", value="AAPL", help="Enter a stock ticker symbol").upper()

        analysis_type = st.selectbox(
            "Analysis Type",
            ["Pattern Detection", "Real-time Signals", "Breakout Scanner", "Technical Analysis"]
        )

        timeframe = st.select_slider(
            "Timeframe",
            options=["1M", "3M", "6M", "1Y"],
            value="3M",
            help="Select the timeframe for analysis"
        )

        # Convert timeframe to days
        timeframe_days = {
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365
        }[timeframe]

        st.divider()

        # Settings
        st.subheader("Settings")
        show_patterns = st.checkbox("Show Pattern Overlays", value=True)
        show_indicators = st.checkbox("Show Technical Indicators", value=False)
        dark_mode = st.checkbox("Dark Mode", value=False)
        st.session_state['dark_mode'] = dark_mode

        st.divider()

        # Info section
        st.info(
            "**Free Deployment Options:**\n"
            "- Streamlit Cloud\n"
            "- Render.com\n"
            "- Railway.app\n"
            "- Fly.io"
        )

    # Main content area
    if analysis_type == "Pattern Detection":
        st.header(f"Pattern Detection: {symbol}")

        col1, col2, col3 = st.columns(3)

        with st.spinner("Detecting patterns..."):
            pattern, prices = detect_patterns(symbol)

        if pattern:
            # Display pattern metrics
            with col1:
                st.metric("Pattern Phase", pattern.phase.value)
            with col2:
                st.metric("Qualification Days", pattern.qualification_days)
            with col3:
                if hasattr(pattern, 'range_percentage'):
                    st.metric("Range %", f"{pattern.range_percentage:.2f}%")

            if pattern.phase.value == "ACTIVE":
                st.success(f"🎯 Active consolidation pattern detected for {symbol}!")

                # Pattern details
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Upper Boundary", f"${pattern.upper_boundary:.2f}")
                with col2:
                    st.metric("Lower Boundary", f"${pattern.lower_boundary:.2f}")
                with col3:
                    st.metric("Power Target", f"${pattern.power_boundary:.2f}")
                with col4:
                    st.metric("Breakout Ready", f"{pattern.breakout_readiness:.1%}")
            else:
                st.info(f"Pattern in {pattern.phase.value} phase")
        else:
            st.warning(f"No active patterns detected for {symbol}")

        # Display chart
        if prices:
            fig = create_price_chart(prices, symbol, pattern if show_patterns else None)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    elif analysis_type == "Real-time Signals":
        st.header("Real-time Trading Signals")

        # Multi-symbol input
        symbols_input = st.text_input(
            "Enter symbols (comma-separated)",
            value="AAPL,MSFT,TSLA,NVDA",
            help="Enter multiple symbols separated by commas"
        )

        symbols = [s.strip().upper() for s in symbols_input.split(",")]

        if st.button("Generate Signals", type="primary"):
            with st.spinner("Generating signals..."):
                from setup_breakout_system import BreakoutPredictionSystem

                async def get_signals():
                    system = BreakoutPredictionSystem()
                    results = await system.get_realtime_signals(symbols)
                    return results

                results = asyncio.run(get_signals())

                if results and 'signals' in results:
                    signals = results['signals']

                    # Display signals in columns
                    cols = st.columns(min(len(signals), 3))
                    for i, signal in enumerate(signals):
                        with cols[i % 3]:
                            st.markdown(create_signal_card(signal), unsafe_allow_html=True)
                else:
                    st.info("No signals generated")

    elif analysis_type == "Breakout Scanner":
        st.header("Breakout Pattern Scanner")

        # Watchlist
        default_watchlist = ["AAPL", "MSFT", "TSLA", "NVDA", "AMD", "PLTR", "SOFI"]
        watchlist = st.multiselect(
            "Select Symbols to Scan",
            options=default_watchlist + ["SPY", "QQQ", "ARKK", "COIN", "RIVN"],
            default=default_watchlist[:5]
        )

        if st.button("Scan for Breakouts", type="primary"):
            with st.spinner("Scanning for breakout patterns..."):
                from setup_breakout_system import BreakoutPredictionSystem

                async def scan():
                    system = BreakoutPredictionSystem()
                    results = await system.scan_for_breakouts(watchlist)
                    return results

                results = asyncio.run(scan())

                if results and 'breakout_candidates' in results:
                    candidates = results['breakout_candidates']

                    if candidates:
                        st.success(f"Found {len(candidates)} breakout candidates!")

                        # Display candidates in a table
                        df_candidates = pd.DataFrame(candidates)
                        st.dataframe(
                            df_candidates,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No immediate breakout candidates found. Continue monitoring.")

                    # Show summary metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Symbols Scanned", results.get('scanned', 0))
                    with col2:
                        st.metric("Patterns Found", len(candidates))
                    with col3:
                        st.metric("Scan Date", results.get('timestamp', 'N/A'))

    elif analysis_type == "Technical Analysis":
        st.header(f"Technical Analysis: {symbol}")

        with st.spinner("Calculating indicators..."):
            from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

            async def get_technicals():
                provider = EnhancedMarketProvider()
                features = await provider.get_technical_features(symbol)
                return features

            features = asyncio.run(get_technicals())

        if features:
            # Display technical indicators
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Price", f"${features.get('price', 0):.2f}")
                st.metric("SMA 20", f"${features.get('sma_20', 0):.2f}")

            with col2:
                rsi = features.get('rsi_14', 50)
                st.metric("RSI (14)", f"{rsi:.1f}")
                if rsi > 70:
                    st.warning("Overbought")
                elif rsi < 30:
                    st.success("Oversold")

            with col3:
                st.metric("BBW", f"{features.get('bbw', 0):.2f}%")
                st.metric("Volatility", f"{features.get('volatility_20d', 0):.2f}%")

            with col4:
                st.metric("Volume Ratio", f"{features.get('volume_ratio', 0):.2f}x")
                st.metric("20D Change", f"{features.get('price_change_20d', 0):.2f}%")

            # Display chart
            prices = fetch_market_data(symbol, timeframe_days)
            if prices:
                fig = create_price_chart(prices, symbol)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Could not fetch technical data for {symbol}")

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p>StockGPT Pattern Analyzer | AIv3 Pattern Detection | Professional APIs</p>
            <p>Deploy this app for free on Streamlit Cloud, Render, or Railway</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()