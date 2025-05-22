import streamlit as st
import pandas as pd
from datetime import datetime

def create_filter_ui(df):
    """Create and display the advanced filter UI components, return the filter values."""
    with st.expander("Advanced Search Options", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            title_filter = st.text_input("Job Title")
            # Multi-source selection
            all_sources = sorted(df["source"].unique().tolist())
            source_filter = st.multiselect("Source(s)", ["All"] + all_sources, default=["All"])
        with col2:
            company_filter = st.text_input("Company")
            location_filter = st.text_input("Location")
        with col3:
            description_filter = st.text_input("Description")
            link_filter = st.text_input("Link")
        
        # Date range filter (timestamp)
        if "timestamp" in df.columns:
            parsed_timestamps = pd.to_datetime(df["timestamp"], errors="coerce", format='mixed')
            min_date = parsed_timestamps.min()
            max_date = parsed_timestamps.max()
            # Convert to Python datetime
            min_date = min_date.to_pydatetime() if hasattr(min_date, "to_pydatetime") else min_date
            max_date = max_date.to_pydatetime() if hasattr(max_date, "to_pydatetime") else max_date
            date_range = st.slider(
                "Date Range (Timestamp)",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD"
            )
        else:
            date_range = None
    
    # Return all filter values
    return {
        "title": title_filter,
        "company": company_filter,
        "source": source_filter,
        "location": location_filter,
        "description": description_filter,
        "link": link_filter,
        "date_range": date_range
    }

def apply_filters(df, filters):
    """Apply the filters to the dataframe and return the filtered dataframe."""
    filtered = df.copy()
    
    # Title filter
    if filters["title"]:
        filtered = filtered[filtered["title"].str.contains(filters["title"], case=False, na=False)]
    
    # Company filter
    if filters["company"]:
        filtered = filtered[filtered["company"].str.contains(filters["company"], case=False, na=False)]
    
    # Source filter
    if filters["source"] and "All" not in filters["source"]:
        filtered = filtered[filtered["source"].isin(filters["source"])]
    
    # Location filter
    if filters["location"] and "location" in filtered.columns:
        filtered = filtered[filtered["location"].str.contains(filters["location"], case=False, na=False)]
    
    # Description filter
    if filters["description"]:
        filtered = filtered[filtered["description"].str.contains(filters["description"], case=False, na=False)]
    
    # Link filter
    if filters["link"]:
        filtered = filtered[filtered["link"].str.contains(filters["link"], case=False, na=False)]
    
    # Date range filter
    if filters["date_range"] and "timestamp" in filtered.columns:
        filtered["timestamp"] = pd.to_datetime(filtered["timestamp"], errors="coerce", format='mixed')
        filtered = filtered[(filtered["timestamp"] >= filters["date_range"][0]) & 
                            (filtered["timestamp"] <= filters["date_range"][1])]
    
    return filtered 