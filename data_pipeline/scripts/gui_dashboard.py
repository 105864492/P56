import streamlit as st
import pandas as pd
import torch
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Emission Heterogeneous Network")

st.title("🌍 Global Emission Heterogeneous Network Dashboard")

# Load data
@st.cache_data
def load_data():
    countries = pd.read_parquet('data/processed/nodes/countries.parquet')
    years = pd.read_parquet('data/processed/nodes/years.parquet')
    metrics = pd.read_parquet('data/processed/nodes/metrics.parquet')
    country_years = pd.read_parquet('data/processed/nodes/country_years.parquet')
    emits_edges = pd.read_parquet('data/processed/edges/emits_edges.parquet')
    metric_edges = pd.read_parquet('data/processed/edges/metric_edges.parquet')
    
    # Load graph
    graph = torch.load('data/graph_data/emission_graph.pt', weights_only=False)
    
    return countries, years, metrics, country_years, emits_edges, metric_edges, graph

countries, years, metrics, country_years, emits_edges, metric_edges, graph = load_data()

# Sidebar
st.sidebar.header("📊 Network Statistics")
st.sidebar.metric("Countries", len(countries))
st.sidebar.metric("Years", len(years))
st.sidebar.metric("Metrics", len(metrics))
st.sidebar.metric("Total Edges", len(emits_edges) + len(metric_edges))

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Network Overview", "🗺️ Country Explorer", "🔗 Edge Browser", "📈 Time Series"])

with tab1:
    st.header("Heterogeneous Network Structure")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Node Types")
        node_counts = {
            'Country': len(countries),
            'Year': len(years),
            'Metric': len(metrics),
            'Country-Year': len(country_years)
        }
        fig = px.bar(x=list(node_counts.keys()), y=list(node_counts.values()), 
                     title="Node Distribution", color=list(node_counts.keys()))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Edge Types")
        edge_counts = {
            'Emits (Country→Year)': len(emits_edges),
            'Metric Values': len(metric_edges)
        }
        fig = px.pie(values=list(edge_counts.values()), names=list(edge_counts.keys()), 
                     title="Edge Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Sample Network Connections")
    sample_edges = emits_edges.head(10)
    st.dataframe(sample_edges[['src', 'dst']])

with tab2:
    st.header("Explore Countries")
    
    selected_country = st.selectbox("Select Country", countries['country'].tolist())
    
    if selected_country:
        country_code = countries[countries['country'] == selected_country]['iso_code'].iloc[0]
        country_id = f"c_{country_code}"
        
        # Get years for this country
        country_edges = emits_edges[emits_edges['src'] == country_id]
        years_for_country = [int(y.replace('y_', '')) for y in country_edges['dst'].tolist()]
        
        st.subheader(f"📅 Active Years: {len(years_for_country)}")
        st.write(f"From {min(years_for_country)} to {max(years_for_country)}")
        
        # Get metric data
        cy_ids = country_years[country_years['iso_code'] == country_code]['cy_id'].tolist()
        metric_data = metric_edges[metric_edges['src'].isin(cy_ids)]
        
        if len(metric_data) > 0:
            st.subheader("📈 Emission Metrics")
            # Sample metrics for display
            sample_metrics = metric_data.head(20)
            st.dataframe(sample_metrics[['src', 'dst', 'value']])

with tab3:
    st.header("Browse Edges")
    
    edge_type = st.radio("Select Edge Type", ["Emits (Country→Year)", "Metric Values"])
    
    if edge_type == "Emits (Country→Year)":
        rows_to_show = st.slider("Rows to show", 5, 100, 20)
        st.dataframe(emits_edges[['src', 'dst', 'weight']].head(rows_to_show))
        
        # Show distribution
        st.subheader("Edge Distribution by Year")
        years_in_edges = emits_edges['dst'].str.replace('y_', '').astype(int)
        fig = px.histogram(x=years_in_edges, title="Emits Edges per Year")
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        rows_to_show = st.slider("Rows to show", 5, 100, 20)
        st.dataframe(metric_edges[['src', 'dst', 'value']].head(rows_to_show))

with tab4:
    st.header("Temporal Analysis")
    
    # Create time series from emits edges
    edge_years = emits_edges['dst'].str.replace('y_', '').astype(int)
    year_counts = edge_years.value_counts().sort_index()
    
    fig = make_subplots(rows=2, cols=1, subplot_titles=("Active Country-Years Over Time", "Cumulative Growth"))
    
    fig.add_trace(go.Scatter(x=year_counts.index, y=year_counts.values, 
                            mode='lines+markers', name='Active Records'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=year_counts.index, y=year_counts.cumsum(), 
                            mode='lines', name='Cumulative', line=dict(color='orange')), row=2, col=1)
    
    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"📊 Total country-year records: {len(emits_edges)}")

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit + PyTorch Geometric")