# scripts/dashboard.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.config import AUTHORS_PATH, PAPERS_PATH, VENUES_PATH, YEARS_PATH, AUTHOR_WROTE_PATH, PAPER_VENUE_PATH, PAPER_YEAR_PATH
from pyvis.network import Network
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
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

selected_tab = option_menu(
    menu_title=None,  # We hide the title to make it look like a clean website header
    options=["Overview", "Authors", "Venues", "Timeline", "Network Visualizer"],
    icons=["bar-chart-line", "person-badge", "building", "calendar3", "diagram-3"],
    default_index=4,
    orientation="horizontal",  # This is the magic word that moves it to the top!
    styles={
        "container": {"padding": "0!important", "background-color": "transparent"},
        "icon": {"font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#333333"},
        "nav-link-selected": {"background-color": "#ff4b4b"},
    }
)
st.markdown("---")

if selected_tab == "Overview":
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

if selected_tab == "Authors":
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

if selected_tab == "Venues":
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

if selected_tab == "Timeline":
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
    
    
if selected_tab == "Network Visualizer":
    st.header("Interactive Network Visualizer")
    st.markdown("Search for an author to generate their ego-network.")
    
    search_query = st.text_input("Search Author (e.g., Dijkstra)", value="Dijkstra")
    
    if search_query:
        # Case-insensitive partial matching
        results = authors[authors["name"].str.contains(search_query, case=False, na=False)]
        
        if results.empty:
            st.error("Author not found. Please try a different spelling.")
        else:
            selected_name = st.selectbox("Select exact author to graph:", results["name"].tolist())
            
            with st.spinner("Generating physics graph..."):
                author_id = results[results['name'] == selected_name]['author_id'].iloc[0]
                
                # Get papers and venues
                author_papers_edges = author_wrote[author_wrote['author_id'] == author_id]
                paper_ids = author_papers_edges['paper_id'].tolist()
                author_papers = papers[papers['paper_id'].isin(paper_ids)]
                
                paper_venues_edges = paper_venue[paper_venue['paper_id'].isin(paper_ids)]
                venue_ids = paper_venues_edges['venue_id'].tolist()
                author_venues = venues[venues['venue_id'].isin(venue_ids)]

                # --- MODERN KPI CARDS ---
                st.markdown("### Ego-Network Statistics")
                c1, c2, c3 = st.columns(3)
                
                # The border=True creates the elevated card effect
                with c1:
                    st.container(border=True).metric(label="Total Papers", value=len(author_papers))
                with c2:
                    st.container(border=True).metric(label="Total Venues", value=len(author_venues))
                with c3:
                    st.container(border=True).metric(label="Total Nodes", value=1 + len(author_papers) + len(author_venues))
                
                st.markdown("---")

                # Build the PyVis Graph
                net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
                net.add_node(int(author_id), label=selected_name, color="#ff4b4b", size=30, title="Author")
                
                for _, row in author_papers.iterrows():
                    p_id = int(row['paper_id'])
                    title = str(row['title'])
                    net.add_node(p_id, label=title[:20]+"...", color="#4b8bff", size=15, title=f"Paper: {title}")
                    net.add_edge(int(author_id), p_id, label="wrote")
                    
                for _, row in paper_venues_edges.iterrows():
                    p_id = int(row['paper_id'])
                    v_id = int(row['venue_id'])
                    v_name = author_venues[author_venues['venue_id'] == v_id]['name'].values[0]
                    v_node_id = f"v_{v_id}" 
                    
                    net.add_node(v_node_id, label=str(v_name), color="#4bff8b", size=20, title=f"Venue: {v_name}")
                    net.add_edge(p_id, v_node_id, label="published_in")

                # Advanced Physics Configuration
                custom_options = """
                var options = {
                  "interaction": {
                    "navigationButtons": false,
                    "zoomSpeed": 0.4
                  },
                  "physics": {
                    "repulsion": {
                      "centralGravity": 0.1,
                      "springLength": 250,
                      "springConstant": 0.05,
                      "nodeDistance": 300
                    },
                    "solver": "repulsion"
                  }
                }
                """
                net.set_options(custom_options)
                
                net.save_graph("temp_graph.html")
                with open("temp_graph.html", "r", encoding="utf-8") as f:
                    html_data = f.read()
                
                zoom_limiter_script = """
                <script type="text/javascript">
                    setTimeout(function() {
                        network.on("zoom", function (params) {
                            var currentScale = network.getScale();
                            if (currentScale < 0.5) {
                                network.moveTo({scale: 0.5});
                            } else if (currentScale > 3.0) {
                                network.moveTo({scale: 3.0});
                            }
                        });
                    }, 1000);
                </script>
                </body>
                """
                html_data = html_data.replace("</body>", zoom_limiter_script)
                components.html(html_data, height=650)

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit + PyTorch Geometric")

