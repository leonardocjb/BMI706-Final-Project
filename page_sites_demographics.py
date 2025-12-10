import pandas as pd
import streamlit as st
import altair as alt
from data_prep import load_and_preprocess_brca

# --- Page B: Tumor Site + Demographics Map View ---

def page_sites_demographics():
    """
    Tumor site and demographic incidence visualization.
    
    Features:
    - Geographic/demographic filters (country, subtype, race, age group)
    - World/regional map of BRCA cases by country
    - Subtype composition stacked bar for selected country
    - Race distribution for selected country
    - Consistent color encodings across all views
    """
    st.header("Sites & Demographics Map View")
    
    # Load data
    try:
        brca_df = load_and_preprocess_brca("clinical.tsv")
    except:
        st.error("Error: Could not locate clinical.tsv")
        return
    
    # --- Sidebar Filters ---
    st.sidebar.subheader("Filters")
    
    # Race filter
    race_opts = sorted([x for x in brca_df["race"].unique() if pd.notna(x) and x != "Unknown"])
    selected_races = st.sidebar.multiselect(
        "Race",
        race_opts,
        default=race_opts[:3] if len(race_opts) > 0 else []
    )
    
    # Ethnicity filter
    ethnicity_opts = sorted([x for x in brca_df["ethnicity"].unique() if pd.notna(x) and x != "Unknown"])
    selected_ethnicities = st.sidebar.multiselect(
        "Ethnicity",
        ethnicity_opts,
        default=ethnicity_opts[:2] if len(ethnicity_opts) > 0 else []
    )
    
    # Age group filter
    age_group = st.sidebar.selectbox(
        "Age Group",
        ["All Ages", "Young (0-45)", "Adult (45-65)", "Senior (65+)"]
    )
    
    # Gender filter
    gender_opts = sorted([x for x in brca_df["gender"].unique() if pd.notna(x) and x != "Unknown"])
    selected_genders = st.sidebar.multiselect(
        "Gender",
        gender_opts,
        default=gender_opts if len(gender_opts) > 0 else []
    )
    
    # --- Apply Filters ---
    filtered_df = brca_df.copy()
    
    if selected_races:
        filtered_df = filtered_df[filtered_df["race"].isin(selected_races)]
    
    if selected_ethnicities:
        filtered_df = filtered_df[filtered_df["ethnicity"].isin(selected_ethnicities)]
    
    if selected_genders:
        filtered_df = filtered_df[filtered_df["gender"].isin(selected_genders)]
    
    if "Young" in age_group:
        filtered_df = filtered_df[filtered_df["age"] <= 45]
    elif "Adult" in age_group:
        filtered_df = filtered_df[(filtered_df["age"] > 45) & (filtered_df["age"] <= 65)]
    elif "Senior" in age_group:
        filtered_df = filtered_df[filtered_df["age"] > 65]
    
    if filtered_df.empty:
        st.warning("No data matches current filters. Please adjust your selection.")
        return
    
    st.sidebar.metric("Patients in View", len(filtered_df))
    
    # --- Lindsay's View: Geographic & Demographic Incidence ---
    st.subheader("Geographic Incidence & Demographic Composition")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Case Distribution by Demographics**")
        # Simple demographic aggregation (country placeholder with race/ethnicity breakdown)
        demo_counts = filtered_df.groupby(["race", "ethnicity"]).size().reset_index(name="Count")
        demo_counts = demo_counts.sort_values("Count", ascending=False).head(10)
        
        demo_chart = alt.Chart(demo_counts).mark_bar().encode(
            x=alt.X("Count:Q", title="Number of Patients"),
            y=alt.Y("race:N", sort="-x", title="Race"),
            color=alt.Color("ethnicity:N", title="Ethnicity"),
            tooltip=["race", "ethnicity", "Count"]
        ).properties(height=300, title="Top Race/Ethnicity Combinations")
        
        st.altair_chart(demo_chart, use_container_width=True)
    
    with col2:
        st.write("**Age Distribution**")
        age_hist = filtered_df[["age"]].dropna()
        
        if not age_hist.empty:
            age_chart = alt.Chart(age_hist).mark_bar(color="#72b7b2").encode(
                x=alt.X("age:Q", bin=alt.Bin(maxbins=15), title="Age"),
                y=alt.Y("count():Q", title="Count"),
                tooltip=["count()"]
            ).properties(height=300)
            
            st.altair_chart(age_chart, use_container_width=True)
    
    st.divider()
    
    # --- Lucy's View: Tumor Site & Co-occurrence ---
    st.subheader("Tumor Site & Co-occurrence Analysis")
    
    col_site1, col_site2 = st.columns([1, 2])
    
    with col_site1:
        st.write("**Primary Sites**")
        
        # Site distribution
        site_counts = filtered_df["site"].value_counts().reset_index()
        site_counts.columns = ["Site", "Count"]
        site_counts = site_counts[site_counts["Site"] != "Unknown"].head(10)
        
        site_chart = alt.Chart(site_counts).mark_bar(color="#4c78a8").encode(
            x=alt.X("Count:Q", title="Number of Patients"),
            y=alt.Y("Site:N", sort="-x", title="Anatomical Site"),
            tooltip=["Site", "Count"]
        ).properties(height=300)
        
        st.altair_chart(site_chart, use_container_width=True)
        
        # Allow selection of site
        selected_site = st.selectbox(
            "Select site for details",
            ["All"] + list(site_counts["Site"].unique())
        )
    
    with col_site2:
        st.write("**Stage Distribution for Selected Site**")
        
        if selected_site != "All":
            site_filtered = filtered_df[filtered_df["site"] == selected_site]
        else:
            site_filtered = filtered_df
        
        if not site_filtered.empty:
            stage_counts = site_filtered["stage"].value_counts().reset_index()
            stage_counts.columns = ["Stage", "Count"]
            stage_counts = stage_counts[stage_counts["Stage"] != "Unknown"]
            
            if not stage_counts.empty:
                stage_chart = alt.Chart(stage_counts).mark_bar(color="#e15759").encode(
                    x=alt.X("Count:Q", title="Number of Patients"),
                    y=alt.Y("Stage:N", sort="-x", title="Stage"),
                    tooltip=["Stage", "Count"]
                ).properties(height=300, title=f"Stages for {selected_site if selected_site != 'All' else 'All Sites'}")
                
                st.altair_chart(stage_chart, use_container_width=True)
            else:
                st.info("No stage data available for selected site.")
        else:
            st.info("No data for selected site.")
    
    st.divider()
    
    # --- Summary Statistics ---
    st.subheader("Summary Statistics")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.metric("Total Patients", len(filtered_df))
    
    with summary_col2:
        unique_sites = filtered_df["site"].nunique()
        st.metric("Unique Sites", unique_sites)
    
    with summary_col3:
        unique_stages = filtered_df[filtered_df["stage"] != "Unknown"]["stage"].nunique()
        st.metric("Stages Represented", unique_stages)
    
    with summary_col4:
        avg_age = filtered_df["age"].mean()
        st.metric("Avg Age at Diagnosis", f"{avg_age:.1f}")


if __name__ == "__main__":
    page_sites_demographics()
