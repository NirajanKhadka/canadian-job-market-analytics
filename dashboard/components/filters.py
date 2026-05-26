import streamlit as st
from components.db import run_query

def render_filters():
    st.sidebar.title("🍁 Filters")
    st.sidebar.caption("Filters update all charts on this page")

    roles_df  = run_query("SELECT DISTINCT role FROM jobs ORDER BY role")
    cities_df = run_query(
        "SELECT DISTINCT city FROM jobs WHERE city NOT IN ('Unspecified','Remote') ORDER BY city"
    )

    all_roles  = roles_df['role'].tolist()
    all_cities = cities_df['city'].tolist()

    roles = st.sidebar.multiselect(
        "Role", all_roles,
        default=["Data Analyst", "BI Developer", "Data Scientist"]
    )
    cities = st.sidebar.multiselect(
        "City", all_cities,
        default=["Toronto", "Vancouver", "Mississauga", "Calgary", "Montreal"]
    )
    min_salary  = st.sidebar.slider(
        "Min Annual Salary (CAD $)", 0, 200_000, 0, step=5_000, format="$%d"
    )
    remote_only = st.sidebar.checkbox("Remote Only", value=False)

    return {
        "roles":      roles  or all_roles,
        "cities":     cities or all_cities,
        "min_salary": min_salary,
        "remote_only": remote_only,
    }