# scripts/dashboard.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from src.config import AUTHORS_PATH, PAPERS_PATH, VENUES_PATH, YEARS_PATH, AUTHOR_WROTE_PATH, PAPER_VENUE_PATH, PAPER_YEAR_PATH

st.set_page_config(layout="wide", page_title="DBLP Heterogeneous Graph")
st.title("📚 DBLP Heterogeneous Graph Dashboard")

@st.cache_data
def load_data():
    authors      = pd.read_parquet(AUTHORS_PATH)
    papers       = pd.read_parquet(PAPERS_PATH)
    venues       = pd.read_parquet(VENUES_PATH)
    years        = pd.read_parquet(YEARS_PATH)
    author_wrote = pd.read_parquet(AUTHOR_WROTE_PATH)
    paper_venue  = pd.read_parquet(PAPER_VENUE_PATH)
    paper_year   = pd.read_parquet(PAPER_YEAR_PATH)
    return authors, papers, venues, years, author_wrote, paper_venue, paper_year

authors, papers, venues, years, author_wrote, paper_venue, paper_year = load_data()

# --- sidebar ---
st.sidebar.header("📊 Graph Statistics")
st.sidebar.metric("Papers",  f"{len(papers):,}")
st.sidebar.metric("Authors", f"{len(authors):,}")
st.sidebar.metric("Venues",  f"{len(venues):,}")
st.sidebar.metric("Years",   f"{len(years):,}")
st.sidebar.metric("Author→Paper Edges", f"{len(author_wrote):,}")
st.sidebar.metric("Paper→Venue Edges",  f"{len(paper_venue):,}")
st.sidebar.metric("Paper→Year Edges",   f"{len(paper_year):,}")

# --- tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "✍️ Authors", 
    "🏛️ Venues", 
    "📅 Timeline",
    "🌐 Network Visualizer"
])

with tab1:
    st.header("Graph Structure")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Node Types")
        node_counts = {"Paper": len(papers), "Author": len(authors), "Venue": len(venues), "Year": len(years)}
        fig = px.bar(x=list(node_counts.keys()), y=list(node_counts.values()), color=list(node_counts.keys()), title="Node Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Edge Types")
        edge_counts = {"Author→Paper": len(author_wrote), "Paper→Venue": len(paper_venue), "Paper→Year": len(paper_year)}
        fig = px.pie(values=list(edge_counts.values()), names=list(edge_counts.keys()), title="Edge Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sample Papers")
    st.dataframe(papers[["paper_id", "title", "type", "ee"]].head(20))

with tab2:
    st.header("Author Explorer")

    # top authors by paper count
    top_authors = (
        author_wrote.groupby("author_id").size()
        .reset_index(name="paper_count")
        .merge(authors, on="author_id")
        .sort_values("paper_count", ascending=False)
        .head(30)
    )

    st.subheader("Top 30 Authors by Paper Count")
    fig = px.bar(top_authors, x="paper_count", y="name", orientation="h", title="Most Prolific Authors")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Search Author")
    query = st.text_input("Author name")
    if query:
        results = authors[authors["name"].str.contains(query, case=False, na=False)]
        if len(results):
            selected = st.selectbox("Select", results["name"].tolist())
            aid = authors[authors["name"] == selected]["author_id"].iloc[0]
            paper_ids = author_wrote[author_wrote["author_id"] == aid]["paper_id"].tolist()
            st.write(f"{len(paper_ids)} papers")
            st.dataframe(papers[papers["paper_id"].isin(paper_ids)][["title", "type", "ee"]])
        else:
            st.info("No authors found.")

with tab3:
    st.header("Venue Explorer")

    venue_counts = (
        paper_venue.groupby("venue_id").size()
        .reset_index(name="paper_count")
        .merge(venues, on="venue_id")
        .sort_values("paper_count", ascending=False)
    )

    st.subheader("Top 30 Venues by Paper Count")
    fig = px.bar(venue_counts.head(30), x="paper_count", y="name", orientation="h", title="Most Active Venues")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Search Venue")
    vquery = st.text_input("Venue name")
    if vquery:
        results = venues[venues["name"].str.contains(vquery, case=False, na=False)]
        if len(results):
            selected = st.selectbox("Select", results["name"].tolist())
            vid = venues[venues["name"] == selected]["venue_id"].iloc[0]
            paper_ids = paper_venue[paper_venue["venue_id"] == vid]["paper_id"].tolist()
            st.write(f"{len(paper_ids)} papers")
            st.dataframe(papers[papers["paper_id"].isin(paper_ids)][["title", "type", "ee"]].head(50))
        else:
            st.info("No venues found.")

with tab4:
    st.header("Timeline")

    year_counts = (
        paper_year.groupby("year_id").size()
        .reset_index(name="count")
        .merge(years, on="year_id")
        .sort_values("year")
    )

    fig = px.line(year_counts, x="year", y="count", title="Publications per Year", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Papers by Publication Type Over Time")
    type_year = (
        papers[["paper_id", "type"]].merge(paper_year, on="paper_id")
        .merge(years, on="year_id")
        .groupby(["year", "type"]).size()
        .reset_index(name="count")
        .sort_values("year")
    )
    fig2 = px.area(type_year, x="year", y="count", color="type", title="Publication Types Over Time")
    st.plotly_chart(fig2, use_container_width=True)

# ============================================
# NETWORK VISUALIZER TAB
# ============================================
with tab5:
    st.header("🌐 Interactive Network Visualizer")
    st.markdown("Search for an author to generate their ego-network with papers and venues.")
    
    search_query = st.text_input("Search Author (e.g., Dijkstra)", value="Dijkstra")
    
    if search_query:
        with st.spinner("🔍 Searching for author..."):
            results = authors[authors["name"].str.contains(search_query, case=False, na=False)]
        
        if results.empty:
            st.error("Author not found. Please try a different spelling.")
        else:
            selected_name = st.selectbox("Select exact author to graph:", results["name"].tolist())
            
            with st.spinner("🔄 Building ego-network..."):
                author_id = results[results['name'] == selected_name]['author_id'].iloc[0]
                
                # Get author's papers
                author_papers_edges = author_wrote[author_wrote['author_id'] == author_id]
                paper_ids = author_papers_edges['paper_id'].tolist()
                author_papers = papers[papers['paper_id'].isin(paper_ids)]
                
                # Limit to 20 papers for readability
                if len(author_papers) > 20:
                    author_papers = author_papers.head(20)
                    st.warning(f"Showing top 20 of {len(author_papers)} papers")
                
                # Get venues for these papers
                paper_venues_edges = paper_venue[paper_venue['paper_id'].isin(author_papers['paper_id'].tolist())]
                venue_ids = paper_venues_edges['venue_id'].tolist()
                author_venues = venues[venues['venue_id'].isin(venue_ids)]
            
            # Display statistics
            st.markdown("### 📊 Ego-Network Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Papers", len(author_papers))
            with col2:
                st.metric("Total Venues", len(author_venues))
            with col3:
                st.metric("Total Nodes", 1 + len(author_papers) + len(author_venues))
            
            st.markdown("---")
            
            # Build and display network
            with st.spinner("🎨 Rendering interactive network..."):
                # Create graph
                G = nx.Graph()
                
                # Add author node
                G.add_node(selected_name, type="Author", color="#ff4b4b", size=30)
                
                # Add paper nodes
                for _, row in author_papers.iterrows():
                    paper_label = row['title'][:25] + "..." if len(row['title']) > 25 else row['title']
                    G.add_node(paper_label, type="Paper", color="#4b8bff", size=20)
                    G.add_edge(selected_name, paper_label, type="wrote")
                
                # Add venue nodes and connect to papers
                for _, row in author_venues.iterrows():
                    venue_label = row['name'][:20] + "..." if len(row['name']) > 20 else row['name']
                    G.add_node(venue_label, type="Venue", color="#4bff8b", size=25)
                    
                    # Connect venue to its papers
                    venue_papers = paper_venues_edges[paper_venues_edges['venue_id'] == row['venue_id']]
                    for _, vp in venue_papers.iterrows():
                        paper_title = author_papers[author_papers['paper_id'] == vp['paper_id']]['title'].values[0]
                        paper_label = paper_title[:25] + "..." if len(paper_title) > 25 else paper_title
                        G.add_edge(paper_label, venue_label, type="published_in")
                
                # Position nodes using spring layout
                pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
                
                # Prepare node data
                node_x = []
                node_y = []
                node_text = []
                node_colors = []
                node_sizes = []
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(node)
                    
                    node_type = G.nodes[node].get('type', 'Unknown')
                    if node_type == 'Author':
                        node_colors.append('#ff4b4b')
                        node_sizes.append(35)
                    elif node_type == 'Venue':
                        node_colors.append('#4bff8b')
                        node_sizes.append(25)
                    else:  # Paper
                        node_colors.append('#4b8bff')
                        node_sizes.append(20)
                
                # Prepare edge data
                edge_x = []
                edge_y = []
                
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                # Create Plotly figure
                fig = go.Figure()
                
                # Add edges
                fig.add_trace(go.Scatter(
                    x=edge_x, 
                    y=edge_y,
                    mode='lines',
                    line=dict(color='#cccccc', width=1.5),
                    hoverinfo='none',
                    showlegend=False
                ))
                
                # Add nodes
                fig.add_trace(go.Scatter(
                    x=node_x, 
                    y=node_y,
                    mode='markers+text',
                    marker=dict(
                        size=node_sizes,
                        color=node_colors,
                        line=dict(width=2, color='white'),
                        opacity=0.9
                    ),
                    text=node_text,
                    textposition="top center",
                    textfont=dict(size=9, color='black'),
                    hoverinfo='text',
                    hovertemplate='<b>%{text}</b><extra></extra>',
                    showlegend=False
                ))
                
                # Update layout
                fig.update_layout(
                    title=dict(
                        text=f"Ego-Network: {selected_name}",
                        font=dict(size=18)
                    ),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=20, r=20, t=50),
                    xaxis=dict(
                        showgrid=False, 
                        zeroline=False, 
                        showticklabels=False,
                        range=[-1.2, 1.2]
                    ),
                    yaxis=dict(
                        showgrid=False, 
                        zeroline=False, 
                        showticklabels=False,
                        range=[-1.2, 1.2]
                    ),
                    height=650,
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                
                # Display the network
                st.plotly_chart(fig, use_container_width=True)
            
            # Show paper details in expander
            with st.expander("📄 View Paper Details"):
                st.dataframe(
                    author_papers[['title', 'type']],
                    use_container_width=True,
                    height=300
                )
            
            # Show venue details in expander
            with st.expander("🏛️ View Venue Details"):
                st.dataframe(
                    author_venues[['name']],
                    use_container_width=True,
                    height=200
                )

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit + PyTorch Geometric")