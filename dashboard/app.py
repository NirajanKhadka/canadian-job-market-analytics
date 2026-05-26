import streamlit as st
import plotly.express as px
from components.db import run_query
from components.filters import render_filters

st.set_page_config(
    page_title="Canadian Job Market Analytics",
    page_icon="🍁", layout="wide",
    initial_sidebar_state="expanded"
)

f = render_filters()
roles   = f["roles"]
cities  = f["cities"]
min_sal = f["min_salary"]
remote  = f["remote_only"]

params = {"roles": roles, "cities": cities, "min_salary": min_sal}

st.title("🍁 Canadian Data Job Market Analytics")
st.caption("Analyzing **20,462** Canadian data job postings across 4 sources | Python · PostgreSQL · Streamlit")
st.divider()

# ── KPI CARDS ─────────────────────────────────────────────────
summary = run_query("""
    SELECT
        COUNT(*)                                                          AS total_postings,
        COUNT(DISTINCT company)                                           AS unique_companies,
        COUNT(DISTINCT city)                                              AS unique_cities,
        ROUND(AVG(salary_year_avg)::numeric, 0)                          AS avg_salary,
        ROUND(SUM(CASE WHEN remote THEN 1 ELSE 0 END)*100.0/COUNT(*),1)  AS remote_pct,
        (SELECT js.skill FROM job_skills js JOIN jobs j2 ON j2.job_id = js.job_id
         WHERE j2.role = ANY(%(roles)s)
           AND (j2.city = ANY(%(cities)s) OR j2.city IN ('Unspecified','Remote'))
           AND COALESCE(j2.salary_year_avg,0) >= %(min_salary)s
         GROUP BY js.skill ORDER BY COUNT(*) DESC LIMIT 1)               AS top_skill,
        (SELECT city FROM jobs j3
         WHERE j3.city NOT IN ('Unspecified','Remote')
           AND j3.role = ANY(%(roles)s)
           AND (j3.city = ANY(%(cities)s) OR j3.city IN ('Unspecified','Remote'))
           AND COALESCE(j3.salary_year_avg,0) >= %(min_salary)s
         GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1)                   AS top_city,
        (SELECT role FROM jobs j4
         WHERE j4.role = ANY(%(roles)s)
           AND (j4.city = ANY(%(cities)s) OR j4.city IN ('Unspecified','Remote'))
           AND COALESCE(j4.salary_year_avg,0) >= %(min_salary)s
         GROUP BY role ORDER BY COUNT(*) DESC LIMIT 1)                   AS top_role
    FROM jobs
    WHERE role = ANY(%(roles)s)
      AND (city = ANY(%(cities)s) OR city IN ('Unspecified','Remote'))
      AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
""", params=params)

row = summary.iloc[0]
c1,c2,c3,c4 = st.columns(4)
c1.metric("📋 Total Postings",   f"{int(row['total_postings']):,}")
c2.metric("🏢 Unique Companies", f"{int(row['unique_companies']):,}")
c3.metric("🏙️ Cities Covered",  f"{int(row['unique_cities']):,}")
c4.metric("💰 Avg Salary (CAD)", f"${int(row['avg_salary']):,}" if row['avg_salary'] else "N/A")

c5,c6,c7,c8 = st.columns(4)
c5.metric("🌐 Remote Jobs",      f"{row['remote_pct']}%")
c6.metric("🔧 Top Skill",        str(row['top_skill']).title())
c7.metric("📍 Top Hiring City",  str(row['top_city']))
c8.metric("👔 Top Role",         str(row['top_role']))
st.divider()

# ── QUICK CHARTS ──────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Job Postings by Role")
    role_df = run_query("""
        SELECT role, COUNT(*) AS postings FROM jobs
        WHERE role = ANY(%(roles)s)
          AND (city = ANY(%(cities)s) OR city IN ('Unspecified','Remote'))
          AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
        GROUP BY role ORDER BY postings DESC
    """, params=params)
    fig = px.bar(role_df, x='postings', y='role', orientation='h',
                 color='postings', color_continuous_scale='Reds',
                 labels={'postings': 'Job Postings', 'role': ''})
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      margin=dict(l=0,r=0,t=30,b=0), height=350)
    fig.update_yaxes(categoryorder='total ascending')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🏙️ Top 10 Hiring Cities")
    city_df = run_query("""
        SELECT city, COUNT(*) AS postings FROM jobs
        WHERE city NOT IN ('Unspecified','Remote')
          AND role = ANY(%(roles)s)
          AND city = ANY(%(cities)s)
          AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
        GROUP BY city ORDER BY postings DESC LIMIT 10
    """, params=params)
    fig2 = px.bar(city_df, x='postings', y='city', orientation='h',
                  color='postings', color_continuous_scale='Blues',
                  labels={'postings': 'Job Postings', 'city': ''})
    fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                       margin=dict(l=0,r=0,t=30,b=0), height=350)
    fig2.update_yaxes(categoryorder='total ascending')
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("🔧 Top 15 In-Demand Skills")
skills_df = run_query("""
    SELECT js.skill, COUNT(*) AS demand_count
    FROM job_skills js JOIN jobs j ON j.job_id = js.job_id
    WHERE j.role = ANY(%(roles)s)
      AND (j.city = ANY(%(cities)s) OR j.city IN ('Unspecified','Remote'))
      AND COALESCE(j.salary_year_avg, 0) >= %(min_salary)s
    GROUP BY js.skill ORDER BY demand_count DESC LIMIT 15
""", params=params)
fig3 = px.bar(skills_df, x='skill', y='demand_count',
              color='demand_count', color_continuous_scale='Oranges',
              labels={'demand_count': 'Demand Count', 'skill': ''})
fig3.update_layout(coloraxis_showscale=False,
                   margin=dict(l=0,r=0,t=30,b=0), height=320)
st.plotly_chart(fig3, use_container_width=True)
st.caption("Navigate using the sidebar pages for detailed analysis →")