import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from components.db import run_query
from components.filters import render_filters

# ── MUST be first Streamlit call ──────────────────────────────
st.set_page_config(page_title="Skills Analysis", page_icon="🛠️", layout="wide")

# ── FILTERS ───────────────────────────────────────────────────
f = render_filters()
roles     = f["roles"]
min_sal   = f["min_salary"]
remote    = f["remote_only"]

st.title("🛠️ Skills Analysis")
st.caption("Most in-demand skills across Canadian data job postings")
st.info(f"🔍 Filtered: **{len(roles)}** roles | Min salary **${min_sal:,}** | Remote only: **{remote}**")
st.divider()

# ── TOP 25 SKILLS — filtered ───────────────────────────────────
st.subheader("Top 25 In-Demand Skills")
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

fig = px.bar(skills_df, x='demand_count', y='skill', orientation='h',
             color='demand_count', color_continuous_scale='Reds',
             text='demand_count',
             labels={'demand_count': 'Job Postings', 'skill': ''})
fig.update_traces(textposition='outside')
fig.update_layout(coloraxis_showscale=False, height=600)
fig.update_yaxes(categoryorder='total ascending')
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── TOP 8 SKILLS BY ROLE — filtered ───────────────────────────
st.subheader("Top 8 Skills by Role")
selected_role = st.selectbox("Select Role", roles if roles else ["Data Analyst"])

role_skills = run_query("""
    WITH ranked AS (
        SELECT j.role, js.skill, COUNT(*) AS cnt,
               RANK() OVER (PARTITION BY j.role ORDER BY COUNT(*) DESC) AS rnk
        FROM jobs j JOIN job_skills js ON j.job_id = js.job_id
        WHERE j.role = %(role)s
          AND COALESCE(j.salary_year_avg, 0) >= %(min_salary)s
          AND (%(remote)s = FALSE OR j.remote = TRUE)
        GROUP BY j.role, js.skill
    )
    SELECT role, skill, cnt FROM ranked
    WHERE rnk <= 8
    ORDER BY cnt DESC
""", params={"role": selected_role, "min_salary": min_sal, "remote": remote})

if not role_skills.empty:
    fig2 = px.bar(role_skills, x='cnt', y='skill', orientation='h',
                  color='cnt', color_continuous_scale='Blues', text='cnt',
                  labels={'cnt': 'Count', 'skill': ''})
    fig2.update_traces(textposition='outside')
    fig2.update_layout(coloraxis_showscale=False, height=400)
    fig2.update_yaxes(categoryorder='total ascending')
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No data for selected filters.")

st.divider()

# ── KEY TOOLS DEMAND — filtered ────────────────────────────────
st.subheader("⚙️ Key Tool Demand")
tools_df = run_query(f"""
    SELECT js.skill,
           COUNT(*) AS total_demand,
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM jobs), 2) AS pct_jobs
    FROM job_skills js
    JOIN jobs j ON j.job_id = js.job_id
    WHERE js.skill IN ('power bi','sql','python','excel','azure','tableau',
                       'aws','spark','snowflake','databricks','r','sas',
                       'looker','dbt','git')
      AND j.role = ANY(%(roles)s)
      AND COALESCE(j.salary_year_avg, 0) >= %(min_salary)s
      {remote_clause}
    GROUP BY js.skill ORDER BY total_demand DESC
""", params={"roles": roles, "min_salary": min_sal})

col1, col2 = st.columns(2)
with col1:
    fig3 = px.bar(tools_df, x='skill', y='total_demand',
                  color='total_demand', color_continuous_scale='Purples',
                  text='total_demand',
                  labels={'total_demand': 'Job Count', 'skill': 'Tool'})
    fig3.update_traces(textposition='outside')
    fig3.update_layout(coloraxis_showscale=False, height=400)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    fig4 = px.pie(tools_df, names='skill', values='total_demand',
                  title='Tool Share of Filtered Postings',
                  color_discrete_sequence=px.colors.qualitative.Set3)
    fig4.update_layout(height=400)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ── SKILLS CO-OCCURRENCE WITH PYTHON — filtered ────────────────
st.subheader("🐍 Skills Most Often Asked Alongside Python")
co_df = run_query("""
    SELECT js2.skill AS co_skill, COUNT(*) AS co_count
    FROM job_skills js1
    JOIN job_skills js2 ON js1.job_id = js2.job_id AND js2.skill != 'python'
    JOIN jobs j ON j.job_id = js1.job_id
    WHERE js1.skill = 'python'
      AND j.role = ANY(%(roles)s)
      AND COALESCE(j.salary_year_avg, 0) >= %(min_salary)s
    GROUP BY js2.skill ORDER BY co_count DESC LIMIT 15
""", params={"roles": roles, "min_salary": min_sal})

fig5 = px.bar(co_df, x='co_count', y='co_skill', orientation='h',
              color='co_count', color_continuous_scale='Greens', text='co_count',
              labels={'co_count': 'Co-occurrence Count', 'co_skill': ''})
fig5.update_traces(textposition='outside')
fig5.update_layout(coloraxis_showscale=False, height=450)
fig5.update_yaxes(categoryorder='total ascending')
st.plotly_chart(fig5, use_container_width=True)
