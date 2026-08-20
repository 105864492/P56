# scripts/dashboard.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "✍️ Authors", "🏛️ Venues", "📅 Timeline"])

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

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit + PyTorch Geometric")