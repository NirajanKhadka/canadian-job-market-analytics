import streamlit as st
import plotly.express as px
from components.db import run_query
from components.filters import render_filters

st.set_page_config(page_title="Salary Analysis", page_icon="💰", layout="wide")

f = render_filters()
roles   = f["roles"]
cities  = f["cities"]
min_sal = f["min_salary"]
remote  = f["remote_only"]

st.title("💰 Salary Analysis")
st.caption("Based on postings with disclosed salary — ~4.6% of total dataset")
st.info(f"🔍 Filtered: **{len(roles)}** roles | **{len(cities)}** cities | Min **${min_sal:,}** | Remote only: **{remote}**")
st.divider()

# ── SALARY DISTRIBUTION BY ROLE ───────────────────────────────
st.subheader("Salary Distribution by Role")
remote_clause = "AND remote = TRUE" if remote else ""


sal_role = run_query(f"""
    SELECT role, salary_year_avg
    FROM jobs
    WHERE salary_year_avg IS NOT NULL
      AND role = ANY(%(roles)s)
      AND salary_year_avg >= %(min_salary)s
      {remote_clause}
""", params={"roles": roles, "min_salary": min_sal})

if not sal_role.empty:
    fig = px.box(sal_role, x='role', y='salary_year_avg',
                 color='role', points='outliers',
                 labels={'salary_year_avg': 'Annual Salary (CAD)', 'role': ''},
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(showlegend=False, height=450,
                      xaxis={'categoryorder': 'median descending'})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No salary data for selected filters.")

st.divider()

# ── SALARY STATS TABLE ────────────────────────────────────────
st.subheader("Salary Statistics by Role")
stats_df = run_query(f"""
    SELECT
        role,
        COUNT(*) AS job_count,
        ROUND(AVG(salary_year_avg)::numeric, 0)                                        AS avg_salary,
        ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary_year_avg)::numeric, 0) AS p25,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY salary_year_avg)::numeric, 0) AS median,
        ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary_year_avg)::numeric, 0) AS p75,
        ROUND(MAX(salary_year_avg)::numeric, 0)                                        AS max_salary
    FROM jobs
    WHERE salary_year_avg IS NOT NULL
      AND role = ANY(%(roles)s)
      AND salary_year_avg >= %(min_salary)s
      {remote_clause}
    GROUP BY role ORDER BY avg_salary DESC
""", params={"roles": roles, "min_salary": min_sal })

for col in ['avg_salary', 'median', 'p25', 'p75', 'max_salary']:
    stats_df[col] = stats_df[col].apply(lambda x: f"${x:,.0f}" if x == x else "N/A")
st.dataframe(stats_df, use_container_width=True, hide_index=True)

st.divider()

# ── SALARY BY CITY ────────────────────────────────────────────
st.subheader("Average Salary by City")
city_sal = run_query(f"""
    SELECT city,
           COUNT(*) AS job_count,
           ROUND(AVG(salary_year_avg)::numeric, 0) AS avg_salary,
           ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
               (ORDER BY salary_year_avg)::numeric, 0) AS median_salary
    FROM jobs
    WHERE salary_year_avg IS NOT NULL
      AND city NOT IN ('Unspecified','Remote')
      AND city = ANY(%(cities)s)
      AND role = ANY(%(roles)s)
      AND salary_year_avg >= %(min_salary)s
      {remote_clause}
    GROUP BY city HAVING COUNT(*) >= 3
    ORDER BY avg_salary DESC LIMIT 12
""", params={"roles": roles, "cities": cities, "min_salary": min_sal})

if not city_sal.empty:
    fig2 = px.bar(city_sal, x='city', y='avg_salary',
                  color='avg_salary', color_continuous_scale='YlOrRd',
                  text='avg_salary',
                  labels={'avg_salary': 'Avg Salary (CAD)', 'city': ''})
    fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig2.update_layout(coloraxis_showscale=False, height=400)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Not enough salary data for selected cities.")

st.divider()

# ── TOP PAYING SKILLS ─────────────────────────────────────────
st.subheader("💎 Top 15 Highest Paying Skills")
skill_sal = run_query(f"""
    SELECT js.skill,
           COUNT(*) AS job_count,
           ROUND(AVG(j.salary_year_avg)::numeric, 0) AS avg_salary,
           ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
               (ORDER BY j.salary_year_avg)::numeric, 0) AS median_salary
    FROM jobs j JOIN job_skills js ON j.job_id = js.job_id
    WHERE j.salary_year_avg IS NOT NULL
      AND j.role = ANY(%(roles)s)
      AND j.salary_year_avg >= %(min_salary)s
      {remote_clause}
    GROUP BY js.skill HAVING COUNT(*) >= 5
    ORDER BY avg_salary DESC LIMIT 15
""", params={"roles": roles, "min_salary": min_sal})

if not skill_sal.empty:
    fig3 = px.bar(skill_sal, x='avg_salary', y='skill', orientation='h',
                  color='avg_salary', color_continuous_scale='Greens',
                  text='avg_salary',
                  labels={'avg_salary': 'Avg Salary (CAD)', 'skill': ''})
    fig3.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig3.update_layout(coloraxis_showscale=False, height=500)
    fig3.update_yaxes(categoryorder='total ascending')
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── REMOTE VS ON-SITE SALARY ──────────────────────────────────
st.subheader("🌐 Remote vs On-Site Salary")
remote_sal = run_query(f"""
    SELECT
        CASE WHEN remote THEN 'Remote' ELSE 'On-Site' END AS work_type,
        COUNT(*) AS job_count,
        ROUND(AVG(salary_year_avg)::numeric, 0) AS avg_salary,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
            (ORDER BY salary_year_avg)::numeric, 0) AS median_salary
    FROM jobs
    WHERE salary_year_avg IS NOT NULL
      AND role = ANY(%(roles)s)
      AND salary_year_avg >= %(min_salary)s
    GROUP BY remote
""", params={"roles": roles, "min_salary": min_sal})

col1, col2 = st.columns(2)
if not remote_sal.empty:
    for work_type, col in [("Remote", col1), ("On-Site", col2)]:
        row = remote_sal[remote_sal['work_type'] == work_type]
        if not row.empty:
            r = row.iloc[0]
            icon = "🌐" if work_type == "Remote" else "🏢"
            col.metric(f"{icon} {work_type}",
                       f"Avg: ${int(r['avg_salary']):,}",
                       f"Median: ${int(r['median_salary']):,}")
