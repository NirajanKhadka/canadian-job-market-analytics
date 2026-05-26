import streamlit as st
import plotly.express as px
from components.db import run_query
from components.filters import render_filters

st.set_page_config(page_title="City Analysis", page_icon="🏙️", layout="wide")


f = render_filters()
roles   = f["roles"]
cities  = f["cities"]
min_sal = f["min_salary"]
remote  = f["remote_only"]
remote_clause = "AND remote = TRUE" if remote else ""
 

skills_df = run_query(f"""
    SELECT js.skill, COUNT(*) AS demand_count,
           ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
    FROM job_skills js
    JOIN jobs j ON j.job_id = js.job_id
    WHERE j.role = ANY(%(roles)s)
      AND COALESCE(j.salary_year_avg, 0) >= %(min_salary)s
      {remote_clause}
    GROUP BY js.skill ORDER BY demand_count DESC LIMIT 25
""", params={"roles": roles, "min_salary": min_sal})


st.title("🏙️ City & Location Analysis")
st.caption("Top hiring cities and remote work breakdown across Canada")
st.info(f"🔍 Filtered: **{len(roles)}** roles | **{len(cities)}** cities | Min **${min_sal:,}** | Remote only: **{remote}**")
st.divider()

# ── TOP 15 CITIES ─────────────────────────────────────────────
st.subheader("Top 15 Hiring Cities")
city_df = run_query(f"""
    SELECT city, COUNT(*) AS postings,
           ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct_total,
           ROUND(AVG(salary_year_avg)::numeric, 0) AS avg_salary
    FROM jobs
    WHERE city NOT IN ('Unspecified', 'Remote')
      AND city = ANY(%(cities)s)
      AND role = ANY(%(roles)s)
      AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
      {remote_clause}
    GROUP BY city ORDER BY postings DESC LIMIT 15
""", params={"roles": roles, "cities": cities, "min_salary": min_sal })

if not city_df.empty:
    fig = px.bar(city_df, x='postings', y='city', orientation='h',
                 color='postings', color_continuous_scale='Blues',
                 text='postings',
                 labels={'postings': 'Job Postings', 'city': ''})
    fig.update_traces(textposition='outside')
    fig.update_layout(coloraxis_showscale=False, height=520)
    fig.update_yaxes(categoryorder='total ascending')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No city data for selected filters.")

st.divider()

# ── ROLE MIX BY CITY ──────────────────────────────────────────
st.subheader("Role Mix by City")
city_role = run_query(f"""
    SELECT city, role, COUNT(*) AS postings
    FROM jobs
    WHERE city = ANY(%(cities)s)
      AND role = ANY(%(roles)s)
      AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
      {remote_clause}
    GROUP BY city, role ORDER BY city, postings DESC
""", params={"roles": roles, "cities": cities, "min_salary": min_sal})

if not city_role.empty:
    fig2 = px.bar(city_role, x='city', y='postings', color='role',
                  barmode='stack',
                  labels={'postings': 'Job Postings', 'city': '', 'role': 'Role'},
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig2.update_layout(height=450, legend_title='Role')
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── REMOTE VS ON-SITE BY CITY ─────────────────────────────────
st.subheader("🌐 Remote vs On-Site by City")
remote_df = run_query("""
    SELECT city,
           SUM(CASE WHEN remote THEN 1 ELSE 0 END)     AS remote_count,
           SUM(CASE WHEN NOT remote THEN 1 ELSE 0 END) AS onsite_count,
           COUNT(*) AS total,
           ROUND(SUM(CASE WHEN remote THEN 1 ELSE 0 END)
               * 100.0 / COUNT(*), 1) AS remote_pct
    FROM jobs
    WHERE city NOT IN ('Unspecified','Remote')
      AND city = ANY(%(cities)s)
      AND role =ANY(%(roles)s)
    GROUP BY city HAVING COUNT(*) >= 20
    ORDER BY total DESC LIMIT 12
""", params={"roles": roles, "cities": cities})

if not remote_df.empty:
    fig3 = px.bar(remote_df, x='city',
                  y=['remote_count', 'onsite_count'],
                  barmode='group',
                  labels={'value': 'Job Count', 'city': '', 'variable': 'Type'},
                  color_discrete_map={'remote_count': '#2196F3', 'onsite_count': '#FF5722'})
    fig3.update_layout(height=400, legend_title='Work Type')
    fig3.for_each_trace(lambda t: t.update(
        name={'remote_count': 'Remote', 'onsite_count': 'On-Site'}[t.name]
    ))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── CITY SUMMARY TABLE ────────────────────────────────────────
st.subheader("📋 City Summary Table")
st.dataframe(
    city_df.rename(columns={
        'city': 'City', 'postings': 'Job Postings',
        'pct_total': '% of Total', 'avg_salary': 'Avg Salary (CAD)'
    }),
    use_container_width=True, hide_index=True
)
