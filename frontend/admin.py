"""
StudioBridge Admin Dashboard
개발자 전용 데이터베이스 관리 인터페이스
"""
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, date, time
import os
from decimal import Decimal
import uuid

# Database connection settings
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "StudioBridge"),
    "user": os.getenv("DB_USER", "StudioBridge"),
    "password": os.getenv("DB_PASSWORD", "StudioBridge123"),
}

# Admin password (환경변수로 설정 권장)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234!")

# Table groups for organization
TABLE_GROUPS = {
    "👤 Users & Profiles": [
        "users",
        "instructor_profiles",
        "studio_profiles",
    ],
    "📋 Jobs & Applications": [
        "job_posts",
        "applications",
        "offers",
    ],
    "📄 Contracts & Payments": [
        "contracts",
        "contract_event_logs",
        "payments",
        "payouts",
    ],
    "⚠️ Disputes & Reports": [
        "disputes",
        "reports",
        "blocks",
    ],
    "💬 Communication": [
        "chat_threads",
        "chat_messages",
        "support_tickets",
    ],
    "⭐ Reviews & Ratings": [
        "reviews",
    ],
    "📊 Analytics & Logs": [
        "user_churn_logs",
        "policy_agreements",
    ],
}

def init_session_state():
    """Initialize session state variables"""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    if "selected_table" not in st.session_state:
        st.session_state.selected_table = None
    if "query_result" not in st.session_state:
        st.session_state.query_result = None

def authenticate():
    """Admin authentication"""
    st.markdown("## 🔐 Admin Authentication")

    with st.form("admin_login"):
        password = st.text_input("Admin Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("❌ Invalid password")

def get_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def get_tables():
    """Get all tables from database"""
    conn = get_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
        return tables
    except Exception as e:
        st.error(f"Error fetching tables: {e}")
        return []
    finally:
        conn.close()

def get_table_info(table_name):
    """Get table column information"""
    conn = get_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cur.fetchall()
        return columns
    except Exception as e:
        st.error(f"Error fetching table info: {e}")
        return []
    finally:
        conn.close()

def serialize_value(value):
    """Serialize complex data types for display"""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, uuid.UUID):
        return str(value)
    elif isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    elif isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    else:
        return value

def query_table(table_name, where_clause="", order_by="", limit=100):
    """Query table data"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            query += " ORDER BY created_at DESC"
        query += f" LIMIT {limit}"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        if rows:
            # Serialize complex types
            for row in rows:
                for key, value in row.items():
                    row[key] = serialize_value(value)

            df = pd.DataFrame(rows)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def execute_sql(query, params=None):
    """Execute arbitrary SQL query"""
    conn = get_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)

            # Check if query returns results
            if cur.description:
                results = cur.fetchall()
                conn.commit()
                return results
            else:
                conn.commit()
                return f"Query executed successfully. Rows affected: {cur.rowcount}"
    except Exception as e:
        conn.rollback()
        return f"Error: {e}"
    finally:
        conn.close()

def update_record(table_name, record_id, updates):
    """Update a record in the table"""
    conn = get_connection()
    if not conn:
        return False

    try:
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [record_id]

        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"

        with conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        st.error(f"Update error: {e}")
        return False
    finally:
        conn.close()

def delete_record(table_name, record_id):
    """Delete a record from the table"""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table_name} WHERE id = %s", (record_id,))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        st.error(f"Delete error: {e}")
        return False
    finally:
        conn.close()

def render_table_viewer():
    """Render table data viewer and editor"""
    st.markdown("## 📊 Database Tables")

    # Sidebar for table selection
    with st.sidebar:
        st.markdown("### Select Table")

        for group_name, tables in TABLE_GROUPS.items():
            st.markdown(f"**{group_name}**")
            for table in tables:
                if st.button(table, key=f"btn_{table}", use_container_width=True):
                    st.session_state.selected_table = table

    # Main content area
    if st.session_state.selected_table:
        table = st.session_state.selected_table
        st.markdown(f"### Table: `{table}`")

        # Table info
        with st.expander("📋 Table Schema", expanded=False):
            columns = get_table_info(table)
            if columns:
                schema_df = pd.DataFrame(columns)
                st.dataframe(schema_df)

        # Query builder
        with st.expander("🔍 Query Builder", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                where_clause = st.text_input("WHERE clause", placeholder="e.g., role = 'instructor'")

            with col2:
                order_by = st.text_input("ORDER BY", placeholder="e.g., created_at DESC")

            with col3:
                limit = st.number_input("LIMIT", value=100, min_value=1, max_value=1000)

            if st.button("🔄 Refresh Data", type="primary"):
                df = query_table(table, where_clause, order_by, limit)
                st.session_state.query_result = df

        # Display data
        if st.session_state.query_result is not None and not st.session_state.query_result.empty:
            df = st.session_state.query_result

            st.markdown(f"**Found {len(df)} records**")

            # Data editor
            edited_df = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key=f"editor_{table}"
            )

            # Export options
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

            with col2:
                json_str = df.to_json(orient="records", default_handler=str)
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_str,
                    file_name=f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        elif st.session_state.query_result is not None:
            st.info("No records found")
    else:
        st.info("👈 Select a table from the sidebar to view data")

def render_sql_executor():
    """Render SQL query executor"""
    st.markdown("## 🖥️ SQL Query Executor")

    st.warning("⚠️ **Warning**: Direct SQL execution can modify or delete data. Use with caution!")

    # SQL input
    sql_query = st.text_area(
        "SQL Query",
        height=150,
        placeholder="Enter your SQL query here...\nExample: SELECT * FROM users WHERE role = 'instructor' LIMIT 10"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        execute_btn = st.button("▶️ Execute", type="primary")
    with col2:
        st.caption("Supports SELECT, INSERT, UPDATE, DELETE, and other SQL commands")

    if execute_btn and sql_query:
        with st.spinner("Executing query..."):
            result = execute_sql(sql_query)

            if isinstance(result, list):
                # Query returned results
                if result:
                    df = pd.DataFrame(result)
                    st.success(f"✅ Query executed successfully. Found {len(df)} records.")
                    st.dataframe(df, use_container_width=True)

                    # Export option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download results as CSV",
                        data=csv,
                        file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Query executed successfully. No records returned.")
            elif isinstance(result, str):
                if "Error" in result:
                    st.error(result)
                else:
                    st.success(result)

    # Common queries
    with st.expander("📚 Common Queries", expanded=False):
        st.code("""
-- Get all users with their profiles
SELECT u.*, ip.name as instructor_name, sp.business_name
FROM users u
LEFT JOIN instructor_profiles ip ON u.id = ip.user_id
LEFT JOIN studio_profiles sp ON u.id = sp.user_id;

-- Get active contracts
SELECT c.*, jp.title, ip.name as instructor, sp.business_name as studio
FROM contracts c
JOIN job_posts jp ON c.offer_id IN (SELECT id FROM offers WHERE application_id IN (SELECT id FROM applications WHERE job_post_id = jp.id))
JOIN instructor_profiles ip ON c.instructor_id = ip.id
JOIN studio_profiles sp ON c.studio_id = sp.id
WHERE c.status = 'in_progress';

-- Check deposit balances
SELECT email, role, deposit_balance, deposit_required, is_early_bird, no_show_count
FROM users
WHERE deposit_balance > 0
ORDER BY deposit_balance DESC;

-- Get disputes needing review
SELECT d.*, c.id as contract_id, u1.email as reporter, u2.email as reported
FROM disputes d
JOIN contracts c ON d.contract_id = c.id
JOIN users u1 ON d.reported_by = u1.id
JOIN users u2 ON d.reported_against = u2.id
WHERE d.status IN ('open', 'objected');
        """, language="sql")

def render_statistics():
    """Render database statistics"""
    st.markdown("## 📈 Database Statistics")

    conn = get_connection()
    if not conn:
        return

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # User statistics
            cur.execute("""
                SELECT
                    role,
                    COUNT(*) as count,
                    COUNT(CASE WHEN is_verified THEN 1 END) as verified,
                    COUNT(CASE WHEN is_suspended THEN 1 END) as suspended
                FROM users
                GROUP BY role
            """)
            user_stats = cur.fetchall()

            # Contract statistics
            cur.execute("""
                SELECT
                    status,
                    COUNT(*) as count,
                    SUM(total_amount) as total_value
                FROM contracts
                GROUP BY status
            """)
            contract_stats = cur.fetchall()

            # Job post statistics
            cur.execute("""
                SELECT
                    status,
                    COUNT(*) as count,
                    AVG(hourly_rate) as avg_rate
                FROM job_posts
                GROUP BY status
            """)
            job_stats = cur.fetchall()

            # Dispute statistics
            cur.execute("""
                SELECT
                    status,
                    type,
                    COUNT(*) as count
                FROM disputes
                GROUP BY status, type
            """)
            dispute_stats = cur.fetchall()

        # Display statistics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 👥 User Statistics")
            if user_stats:
                df = pd.DataFrame(user_stats)
                st.dataframe(df, use_container_width=True)

            st.markdown("### 📋 Job Post Statistics")
            if job_stats:
                df = pd.DataFrame(job_stats)
                df['avg_rate'] = df['avg_rate'].apply(lambda x: f"₩{float(x):,.0f}" if x else "N/A")
                st.dataframe(df, use_container_width=True)

        with col2:
            st.markdown("### 📄 Contract Statistics")
            if contract_stats:
                df = pd.DataFrame(contract_stats)
                df['total_value'] = df['total_value'].apply(lambda x: f"₩{float(x):,.0f}" if x else "₩0")
                st.dataframe(df, use_container_width=True)

            st.markdown("### ⚠️ Dispute Statistics")
            if dispute_stats:
                df = pd.DataFrame(dispute_stats)
                st.dataframe(df, use_container_width=True)

        # Recent activity
        st.markdown("### 🕐 Recent Activity")

        tabs = st.tabs(["Recent Users", "Recent Contracts", "Recent Disputes"])

        with tabs[0]:
            recent_users = query_table("users", "", "created_at DESC", 10)
            if not recent_users.empty:
                st.dataframe(recent_users[['email', 'role', 'created_at', 'is_verified', 'deposit_balance']], use_container_width=True)

        with tabs[1]:
            recent_contracts = query_table("contracts", "", "created_at DESC", 10)
            if not recent_contracts.empty:
                st.dataframe(recent_contracts[['id', 'status', 'total_amount', 'created_at']], use_container_width=True)

        with tabs[2]:
            recent_disputes = query_table("disputes", "", "created_at DESC", 10)
            if not recent_disputes.empty:
                st.dataframe(recent_disputes[['id', 'type', 'status', 'created_at', 'objection_deadline']], use_container_width=True)

    except Exception as e:
        st.error(f"Error loading statistics: {e}")
    finally:
        conn.close()

def main():
    st.set_page_config(
        page_title="StudioBridge Admin",
        page_icon="🛠️",
        layout="wide"
    )

    st.markdown("# 🛠️ StudioBridge Admin Dashboard")
    st.caption("Database Management Interface - Developer Only")

    init_session_state()

    # Authentication check
    if not st.session_state.admin_authenticated:
        authenticate()
        return

    # Logout button
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.admin_authenticated = False
            st.rerun()

    # Main navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Tables", "🖥️ SQL Executor", "📈 Statistics", "⚙️ Utilities"])

    with tab1:
        render_table_viewer()

    with tab2:
        render_sql_executor()

    with tab3:
        render_statistics()

    with tab4:
        st.markdown("## ⚙️ Database Utilities")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 🔄 Reset Test Data")
            if st.button("Delete All Test Accounts", type="secondary"):
                if st.checkbox("I understand this will delete all test accounts"):
                    result = execute_sql("""
                        DELETE FROM users
                        WHERE email LIKE '%test.com%'
                        OR email LIKE 'instructor_%'
                        OR email LIKE 'studio_%'
                        OR email LIKE '%debug%'
                    """)
                    st.info(result)

        with col2:
            st.markdown("### 🗑️ Clear Old Data")
            days = st.number_input("Delete data older than (days)", value=30, min_value=1)
            if st.button("Clear Old Disputes", type="secondary"):
                result = execute_sql(f"""
                    DELETE FROM disputes
                    WHERE created_at < NOW() - INTERVAL '{days} days'
                    AND status = 'resolved'
                """)
                st.info(result)

        with col3:
            st.markdown("### 💾 Database Info")
            conn = get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT version()")
                        version = cur.fetchone()[0]
                        st.info(f"PostgreSQL: {version.split(',')[0]}")

                        cur.execute("""
                            SELECT
                                pg_database_size(current_database()) as size
                        """)
                        size = cur.fetchone()[0]
                        st.info(f"Database Size: {size / 1024 / 1024:.2f} MB")
                finally:
                    conn.close()

if __name__ == "__main__":
    main()