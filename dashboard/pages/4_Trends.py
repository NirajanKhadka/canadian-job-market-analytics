import streamlit as st
import plotly.express as px
from components.db import run_query
from components.filters import render_filters

st.set_page_config(page_title="Trends", page_icon="📈", layout="wide")

# ── FILTERS ───────────────────────────────────────────────────
f = render_filters()
roles   = f["roles"]
cities  = f["cities"]
min_sal = f["min_salary"]
remote  = f["remote_only"]
remote_clause = "AND remote = TRUE" if remote else ""

params = {"roles": roles, "cities": cities, "min_salary": min_sal, "remote": remote}

st.title("📈 Job Market Trends")
st.caption("Monthly posting volume, role trends, seniority and schedule breakdown")
st.info(f"🔍 Filtered: **{len(roles)}** roles | **{len(cities)}** cities | Min **${min_sal:,}** | Remote only: **{remote}**")
st.divider()

# ── MONTHLY POSTING VOLUME ────────────────────────────────────
st.subheader("Monthly Job Posting Volume")
monthly_df = run_query("""
    SELECT
        EXTRACT(YEAR  FROM posted_date)::int         AS year,
        EXTRACT(MONTH FROM posted_date)::int         AS month,
        TO_CHAR(posted_date, 'Mon YYYY')             AS month_label,
        COUNT(*)                                     AS postings,
        SUM(COUNT(*)) OVER (
            ORDER BY EXTRACT(YEAR  FROM posted_date),
                     EXTRACT(MONTH FROM posted_date)
        )                                            AS running_total
    FROM jobs
    WHERE posted_date IS NOT NULL
      AND role = ANY(%(roles)s)
      AND (city = ANY(%(cities)s) OR city IN ('Unspecified','Remote'))
      AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
      AND (%(remote)s = FALSE OR remote = TRUE)
    GROUP BY
        EXTRACT(YEAR  FROM posted_date),
        EXTRACT(MONTH FROM posted_date),
        TO_CHAR(posted_date, 'Mon YYYY')
    ORDER BY year, month
""", params=params)

if not monthly_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(monthly_df, x='month_label', y='postings',
                     color='postings', color_continuous_scale='Blues',
                     labels={'postings': 'Job Postings', 'month_label': ''},
                     title='Monthly Postings')
        fig.update_layout(coloraxis_showscale=False, height=350,
                          xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.line(monthly_df, x='month_label', y='running_total',
                       markers=True,
                       labels={'running_total': 'Cumulative Postings',
                               'month_label': ''},
                       title='Cumulative Posting Growth')
        fig2.update_traces(line_color='#FF5722', line_width=3)
        fig2.update_layout(height=350, xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("No posting date data available for selected filters.")

st.divider()

# ── MONTHLY TREND BY ROLE ─────────────────────────────────────
st.subheader("Monthly Postings by Role")
role_monthly = run_query("""
    SELECT
        EXTRACT(YEAR  FROM posted_date)::int AS year,
        EXTRACT(MONTH FROM posted_date)::int AS month,
        TO_CHAR(posted_date, 'Mon YYYY')     AS month_label,
        role,
        COUNT(*)                             AS postings
    FROM jobs
    WHERE posted_date IS NOT NULL
      AND role = ANY(%(roles)s)
      AND (city = ANY(%(cities)s) OR city IN ('Unspecified','Remote'))
      AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
      AND (%(remote)s = FALSE OR remote = TRUE)
    GROUP BY
        EXTRACT(YEAR  FROM posted_date),
        EXTRACT(MONTH FROM posted_date),
        TO_CHAR(posted_date, 'Mon YYYY'),
        role
    ORDER BY year, month
""", params=params)

if not role_monthly.empty:
    fig3 = px.line(role_monthly, x='month_label', y='postings',
                   color='role', markers=True,
                   labels={'postings': 'Postings', 'month_label': '', 'role': 'Role'},
                   color_discrete_sequence=px.colors.qualitative.Set1)
    fig3.update_layout(height=420, xaxis_tickangle=-45, legend_title='Role')
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("No role trend data for selected filters.")

st.divider()


# ── SENIORITY BREAKDOWN ───────────────────────────────────────
st.subheader("👔 Seniority Level Breakdown")
seniority_df = run_query(f"""
    SELECT seniority, COUNT(*) AS postings,
           ROUND(AVG(salary_year_avg)::numeric, 0) AS avg_salary
    FROM (
        SELECT
            salary_year_avg,
            CASE
                WHEN LOWER(job_title) LIKE '%%senior%%'
                  OR LOWER(job_title) LIKE '%%sr.%%'       THEN 'Senior'
                WHEN LOWER(job_title) LIKE '%%junior%%'
                  OR LOWER(job_title) LIKE '%%jr.%%'       THEN 'Junior'
                WHEN LOWER(job_title) LIKE '%%lead%%'
                  OR LOWER(job_title) LIKE '%%principal%%' THEN 'Lead/Principal'
                WHEN LOWER(job_title) LIKE '%%intern%%'    THEN 'Intern'
                ELSE 'Mid-level'
            END AS seniority
        FROM jobs
        WHERE role = ANY(%(roles)s)
          AND (city = ANY(%(cities)s) OR city IN ('Unspecified','Remote'))
          AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
          {remote_clause}
    ) sub
    GROUP BY seniority
    ORDER BY postings DESC
""", params={"roles": roles, "cities": cities, "min_salary": min_sal})


if not seniority_df.empty:
    col3, col4 = st.columns(2)
    with col3:
        fig4 = px.pie(seniority_df, names='seniority', values='postings',
                      title='Postings by Seniority',
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig4.update_traces(textinfo='label+percent')
        fig4.update_layout(height=380)
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        sal_df = seniority_df.dropna(subset=['avg_salary'])
        if not sal_df.empty:
            fig5 = px.bar(sal_df, x='seniority', y='avg_salary',
                          color='avg_salary', color_continuous_scale='YlOrRd',
                          text='avg_salary', title='Avg Salary by Seniority',
                          labels={'avg_salary': 'Avg Salary (CAD)', 'seniority': ''})
            fig5.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig5.update_layout(coloraxis_showscale=False, height=380)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No salary data available for seniority breakdown.")

st.divider()



# ── SCHEDULE TYPE ─────────────────────────────────────────────
st.subheader("⏱️ Schedule Type Distribution")
sched_df = run_query(f"""
    SELECT
        COALESCE(schedule_type, 'Unknown') AS schedule_type,
        COUNT(*)                           AS count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
    FROM jobs
    WHERE role = ANY(%(roles)s)
      AND (city = ANY(%(cities)s) OR city IN ('Unspecified','Remote'))
      AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
      {remote_clause}
    GROUP BY schedule_type
    ORDER BY count DESC
""", params=params)

if not sched_df.empty:
    col5, col6 = st.columns(2)
    with col5:
        fig6 = px.pie(sched_df, names='schedule_type', values='count',
                      title='Full-time vs Contract vs Part-time',
                      color_discrete_sequence=px.colors.qualitative.Set3)
        fig6.update_traces(textinfo='label+percent')
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True)

    with col6:
        fig7 = px.bar(sched_df, x='schedule_type', y='count',
                      color='count', color_continuous_scale='Purples',
                      text='count',
                      labels={'count': 'Job Count', 'schedule_type': ''})
        fig7.update_traces(textposition='outside')
        fig7.update_layout(coloraxis_showscale=False, height=400)
        st.plotly_chart(fig7, use_container_width=True)
else:
    st.warning("No schedule type data for selected filters.")

st.divider()

# ── TOP COMPANIES BY POSTINGS ─────────────────────────────────
st.subheader("🏢 Top 15 Hiring Companies")
company_df = run_query(f"""
    SELECT company, COUNT(*) AS postings,
           ROUND(AVG(salary_year_avg)::numeric, 0) AS avg_salary
    FROM jobs
    WHERE company IS NOT NULL
      AND role = ANY(%(roles)s)
      AND (city = ANY(%(cities)s) OR city IN ('Unspecified','Remote'))
      AND COALESCE(salary_year_avg, 0) >= %(min_salary)s
      {remote_clause}
    GROUP BY company
    ORDER BY postings DESC LIMIT 15
""", params=params)

if not company_df.empty:
    fig8 = px.bar(company_df, x='postings', y='company', orientation='h',
                  color='postings', color_continuous_scale='Teal',
                  text='postings',
                  labels={'postings': 'Job Postings', 'company': ''})
    fig8.update_traces(textposition='outside')
    fig8.update_layout(coloraxis_showscale=False, height=520)
    fig8.update_yaxes(categoryorder='total ascending')
    st.plotly_chart(fig8, use_container_width=True)