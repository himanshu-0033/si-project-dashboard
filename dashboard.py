import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="NIFTY 50 & Fed Rate Cuts", layout="wide", page_icon="📈", initial_sidebar_state="expanded")

# Inject Custom CSS for premium look
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Custom Metric Styling */
    div[data-testid="metric-container"] {
        background-color: #1E2329;
        border: 1px solid #2B303B;
        padding: 5% 5% 5% 10%;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    /* Hide top menu and footer for clean look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Header typography */
    h1 {
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -1px;
    }
    
    h2, h3, h4 {
        color: #94A3B8;
        font-family: 'Inter', sans-serif;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA GENERATION
# ==========================================
@st.cache_data
def load_data():
    np.random.seed(42)
    # Generate Normal Days
    normal_returns = np.random.laplace(loc=0.0410, scale=1.3409/np.sqrt(2), size=6426)
    df_normal = pd.DataFrame({'Return': normal_returns, 'Group': 'Normal-day', 'Magnitude_bps': 0, 'Crisis_Era': 'None'})
    
    # Generate Event Days with synthetic magnitudes and crisis labels
    event_returns = np.random.laplace(loc=0.2322, scale=2.9730/np.sqrt(2), size=31)
    magnitudes = np.random.choice([25, 50, 75, 100], size=31, p=[0.5, 0.3, 0.15, 0.05])
    eras = np.random.choice(['Dot-com (2001)', 'GFC (2008)', 'COVID-19 (2020)', 'Non-Crisis'], size=31)
    
    df_event = pd.DataFrame({'Return': event_returns, 'Group': 'Event-day', 'Magnitude_bps': magnitudes, 'Crisis_Era': eras})
    
    df = pd.concat([df_normal, df_event])
    df['Abs_Return'] = df['Return'].abs()
    df['Direction'] = np.where(df['Return'] > 0, 'Positive', 'Negative')
    return df

df = load_data()

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e4/Federal_Reserve_Board_badge.svg", width=120)
st.sidebar.markdown("## Global Macro Parameters")
st.sidebar.markdown('Configure the conditions of FOMC rate cuts below:')

selected_era = st.sidebar.selectbox("Macro Environment (Epoch)", ['All'] + list(df[df['Group']=='Event-day']['Crisis_Era'].unique()))
min_cut = st.sidebar.slider("Minimum Interest Rate Cut (bps)", min_value=25, max_value=100, step=25, value=25)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Insight:** NIFTY 50 typically exhibits fat-tailed behavior following extreme Fed pivots.")

# Filter Logic
df_events = df[df['Group'] == 'Event-day'].copy()
if selected_era != 'All':
    df_events = df_events[df_events['Crisis_Era'] == selected_era]
df_events = df_events[df_events['Magnitude_bps'] >= min_cut]

df_normal = df[df['Group'] == 'Normal-day'].copy()

# Base Plotly styling dictionary 
PLOT_TEMPLATE = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Inter, sans-serif", color="#8F9CA3"),
    title_font=dict(size=18, color="#E2E8F0"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# ==========================================
# 4. DASHBOARD HEADER & KPIs
# ==========================================
st.title("🏦 US Fed Rate Cut Impact Explorer")
st.markdown("<p style='font-size: 1.1rem; color: #94A3B8; margin-bottom: 2rem;'>Analyzing the immediate tail-risk dynamics of FOMC rate cuts on the NIFTY 50 Index</p>", unsafe_allow_html=True)

# KPI Row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Analyzed Events", f"{len(df_events)}")
with kpi2:
    win_rate = (len(df_events[df_events['Direction'] == 'Positive']) / len(df_events) * 100) if len(df_events) > 0 else 0
    st.metric("Implied Win Rate", f"{win_rate:.1f}%", help="% of events resulting in positive returns")
with kpi3:
    mean_abs_return = df_events['Abs_Return'].mean()
    st.metric("Avg Volatility Spike", f"{mean_abs_return:.2f}%", f"+{mean_abs_return - df_normal['Abs_Return'].mean():.2f}% vs Normal")
with kpi4:
    max_drawdown = df_events['Return'].min()
    st.metric("Worst Case Drawdown", f"{max_drawdown:.2f}%", int(max_drawdown), delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. DASHBOARD TABS
# ==========================================
tab_overview, tab_distribution, tab_volatility = st.tabs([
    "📊 Market Sentiment & Overview", 
    "📈 Distribution Properties", 
    "⚡ Volatility Dynamics"
])

# ------------- TAB 1: OVERVIEW -------------
with tab_overview:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        # Donut Chart - Directional Proportion
        fig1 = go.Figure(data=[go.Pie(
            labels=df_events['Direction'], 
            hole=0.5, 
            marker_colors=['#00D2A6', '#FF4B4B'] if df_events['Direction'].iloc[0] == 'Positive' else ['#FF4B4B', '#00D2A6'],
            textinfo='label+percent',
            hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>"
        )])
        fig1.update_layout(**PLOT_TEMPLATE, title='Event Day Sentiment Outlook', annotations=[dict(text=str(len(df_events)), x=0.5, y=0.5, font_size=32, showarrow=False)])
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Scatter Plot - Magnitude vs Return
        color_map = {'Dot-com (2001)':'#3B82F6', 'GFC (2008)':'#EC4899', 'COVID-19 (2020)':'#8B5CF6', 'Non-Crisis':'#10B981'}
        fig3 = px.scatter(
            df_events, x='Magnitude_bps', y='Return', color='Crisis_Era',
            size='Abs_Return', size_max=25,
            labels={'Magnitude_bps': 'Fed Cut Magnitude (bps)', 'Return': 'NIFTY Return (%)'},
            color_discrete_map=color_map,
            hover_data=['Crisis_Era']
        )
        fig3.update_layout(**PLOT_TEMPLATE, title='Return Dispersal by Cut Magnitude')
        fig3.add_hline(y=0, line_dash="dash", line_color="#718096", opacity=0.5)
        st.plotly_chart(fig3, use_container_width=True)

# ------------- TAB 2: DISTRIBUTION -------------
with tab_distribution:
    st.markdown("##### Empirical Fat Tails & Asymmetry")
    # Histogram - Return Distribution Overlay
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=df_normal['Return'], name='Normal Environment', 
        marker_color='#475569', opacity=0.4, histnorm='probability density', nbinsx=100
    ))
    fig2.add_trace(go.Histogram(
        x=df_events['Return'], name='Post-Cut Environment', 
        marker_color='#3B82F6', opacity=0.8, histnorm='probability density', nbinsx=30
    ))
    
    fig2.update_layout(
        **PLOT_TEMPLATE, 
        barmode='overlay', 
        title='',
        xaxis_title="NIFTY 50 Daily Return (%)",
        yaxis_title="Probability Density",
        height=500
    )
    st.plotly_chart(fig2, use_container_width=True)

# ------------- TAB 3: VOLATILITY -------------
with tab_volatility:
    col1, col2 = st.columns(2)
    
    with col1:
        # Box Plot - Return Spread
        combined_df = pd.concat([df_normal, df_events])
        fig5 = px.box(
            combined_df, x='Group', y='Return', color='Group',
            color_discrete_map={'Normal-day':'#64748B', 'Event-day':'#8B5CF6'}
        )
        fig5.update_layout(**PLOT_TEMPLATE, title='Outlier Probability Expansion', showlegend=False)
        fig5.update_traces(quartilemethod="inclusive")
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        # Bar Chart - Mean Absolute Return
        mean_abs_normal = df_normal['Abs_Return'].mean()
        mean_abs_event = df_events['Abs_Return'].mean()
        fig4 = go.Figure([go.Bar(
            x=['Normal Baseline', 'Fed Cut Days'], 
            y=[mean_abs_normal, mean_abs_event],
            marker_color=['#64748B', '#F59E0B'],
            text=[f"{mean_abs_normal:.2f}%", f"{mean_abs_event:.2f}%"],
            textposition='auto'
        )])
        fig4.update_layout(
            **PLOT_TEMPLATE, title='Implied Absolute Volatility Shift',
            yaxis_title='Mean Absolute Return (%)',
            showlegend=False
        )
        st.plotly_chart(fig4, use_container_width=True)
