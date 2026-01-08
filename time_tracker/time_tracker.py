import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import os

# File paths
CLIENTS_FILE = 'clients.csv'
TIME_ENTRIES_FILE = 'time_entries.csv'
INVOICES_FILE = 'invoices.csv'
SETTINGS_FILE = 'settings.csv'
NON_WORK_DAYS_FILE = 'non_work_days.csv'

# Initialize data files
def initialize_files():
    try:
        if not os.path.exists(CLIENTS_FILE):
            pd.DataFrame(columns=['client_name', 'hourly_rate', 'billing_type', 'active', 'has_hour_limit', 'limit_type', 'hour_limit', 'contract_start_date']).to_csv(CLIENTS_FILE, index=False)
        
        if not os.path.exists(TIME_ENTRIES_FILE):
            pd.DataFrame(columns=['date', 'client_name', 'hours', 'notes']).to_csv(TIME_ENTRIES_FILE, index=False)
        
        if not os.path.exists(INVOICES_FILE):
            pd.DataFrame(columns=['date', 'client_name', 'amount', 'type', 'description']).to_csv(INVOICES_FILE, index=False)
        
        if not os.path.exists(SETTINGS_FILE):
            pd.DataFrame({'monthly_target': [8000.0], 'work_days': ['Monday,Tuesday,Wednesday,Thursday,Friday']}).to_csv(SETTINGS_FILE, index=False)
        
        if not os.path.exists(NON_WORK_DAYS_FILE):
            pd.DataFrame(columns=['date', 'reason']).to_csv(NON_WORK_DAYS_FILE, index=False)
    except Exception as e:
        st.error(f"Error initializing files: {str(e)}")

# Load data
def load_clients():
    try:
        df = pd.read_csv(CLIENTS_FILE)
        if df.empty:
            return pd.DataFrame(columns=['client_name', 'hourly_rate', 'billing_type', 'active', 'has_hour_limit', 'limit_type', 'hour_limit', 'contract_start_date'])
        
        # Add new columns if they don't exist (for backwards compatibility)
        if 'billing_type' not in df.columns:
            df['billing_type'] = 'Hourly'
        if 'has_hour_limit' not in df.columns:
            df['has_hour_limit'] = False
        if 'limit_type' not in df.columns:
            df['limit_type'] = 'None'
        if 'hour_limit' not in df.columns:
            df['hour_limit'] = 0
        if 'contract_start_date' not in df.columns:
            df['contract_start_date'] = None
        
        df['hourly_rate'] = df['hourly_rate'].fillna(0)
        df['hour_limit'] = df['hour_limit'].fillna(0)
        df['has_hour_limit'] = df['has_hour_limit'].fillna(False)
        
        return df
    except Exception as e:
        st.error(f"Error loading clients: {str(e)}")
        return pd.DataFrame(columns=['client_name', 'hourly_rate', 'billing_type', 'active', 'has_hour_limit', 'limit_type', 'hour_limit', 'contract_start_date'])

def load_time_entries():
    try:
        df = pd.read_csv(TIME_ENTRIES_FILE)
        if df.empty:
            return pd.DataFrame(columns=['date', 'client_name', 'hours', 'notes'])
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        st.error(f"Error loading time entries: {str(e)}")
        return pd.DataFrame(columns=['date', 'client_name', 'hours', 'notes'])

def load_invoices():
    try:
        df = pd.read_csv(INVOICES_FILE)
        if df.empty:
            return pd.DataFrame(columns=['date', 'client_name', 'amount', 'type', 'description'])
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        st.error(f"Error loading invoices: {str(e)}")
        return pd.DataFrame(columns=['date', 'client_name', 'amount', 'type', 'description'])

def load_settings():
    try:
        df = pd.read_csv(SETTINGS_FILE)
        if df.empty:
            return {'monthly_target': 15000.0, 'work_days': 'Monday,Tuesday,Wednesday,Thursday,Friday'}
        return df.iloc[0]
    except Exception as e:
        st.error(f"Error loading settings: {str(e)}")
        return {'monthly_target': 15000.0, 'work_days': 'Monday,Tuesday,Wednesday,Thursday,Friday'}

def load_non_work_days():
    try:
        df = pd.read_csv(NON_WORK_DAYS_FILE)
        if df.empty:
            return pd.DataFrame(columns=['date', 'reason'])
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    except Exception as e:
        st.error(f"Error loading non-work days: {str(e)}")
        return pd.DataFrame(columns=['date', 'reason'])

# Save data
def save_clients(df):
    df.to_csv(CLIENTS_FILE, index=False)

def save_time_entries(df):
    df.to_csv(TIME_ENTRIES_FILE, index=False)

def save_invoices(df):
    df.to_csv(INVOICES_FILE, index=False)

def save_settings(monthly_target, work_days):
    pd.DataFrame({'monthly_target': [monthly_target], 'work_days': [','.join(work_days)]}).to_csv(SETTINGS_FILE, index=False)

def save_non_work_days(df):
    df.to_csv(NON_WORK_DAYS_FILE, index=False)

# Calculate client hours
def calculate_client_hours(client_name, time_entries_df, limit_type, contract_start_date=None, year=None, month=None):
    """Calculate hours used for a client based on their limit type"""
    if time_entries_df.empty:
        return 0
    
    client_entries = time_entries_df[time_entries_df['client_name'] == client_name]
    
    if client_entries.empty:
        return 0
    
    # If limit_type is None or empty, default to Monthly calculation
    if pd.isna(limit_type) or limit_type == 'None' or limit_type == '':
        limit_type = 'Monthly'
    
    if limit_type == 'Monthly':
        # Calculate hours for the specified month (or current month if not specified)
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        month_start = datetime(year, month, 1)
        month_end = datetime(year, month, calendar.monthrange(year, month)[1])
        month_entries = client_entries[(client_entries['date'] >= month_start) & (client_entries['date'] <= month_end)]
        return month_entries['hours'].sum()
    
    elif limit_type == 'Contract Total':
        # Calculate hours since contract start (all time from contract start)
        if contract_start_date:
            try:
                start_date = pd.to_datetime(contract_start_date)
                contract_entries = client_entries[client_entries['date'] >= start_date]
                return contract_entries['hours'].sum()
            except:
                return client_entries['hours'].sum()
        else:
            # If no start date specified, count all entries
            return client_entries['hours'].sum()
    
    # Default fallback to monthly if unknown limit type
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    month_start = datetime(year, month, 1)
    month_end = datetime(year, month, calendar.monthrange(year, month)[1])
    month_entries = client_entries[(client_entries['date'] >= month_start) & (client_entries['date'] <= month_end)]
    return month_entries['hours'].sum()

# Calculate metrics
def is_work_day(date, work_days_list, non_work_days_df):
    if calendar.day_name[date.weekday()] not in work_days_list:
        return False
    
    if not non_work_days_df.empty:
        if date in non_work_days_df['date'].values:
            return False
    
    return True

def get_work_days_in_month(year, month, work_days, non_work_days_df):
    days_in_month = calendar.monthrange(year, month)[1]
    work_day_names = work_days
    work_days_count = 0
    
    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day).date()
        if is_work_day(date, work_day_names, non_work_days_df):
            work_days_count += 1
    
    return work_days_count

def calculate_monthly_stats(year, month, clients_df, time_entries_df, invoices_df, settings, non_work_days_df):
    month_start = datetime(year, month, 1)
    month_end = datetime(year, month, calendar.monthrange(year, month)[1])
    
    # Filter data for the month
    monthly_entries = time_entries_df[
        (time_entries_df['date'] >= month_start) & 
        (time_entries_df['date'] <= month_end)
    ] if not time_entries_df.empty else pd.DataFrame()
    
    monthly_invoices = invoices_df[
        (invoices_df['date'] >= month_start) & 
        (invoices_df['date'] <= month_end)
    ] if not invoices_df.empty else pd.DataFrame()
    
    # Calculate hourly billables (only for hourly clients)
    hourly_total = 0
    total_hours = 0
    if not monthly_entries.empty and not clients_df.empty:
        hourly_clients = clients_df[clients_df['billing_type'] == 'Hourly']
        if not hourly_clients.empty:
            merged = monthly_entries.merge(hourly_clients[['client_name', 'hourly_rate']], on='client_name', how='inner')
            if not merged.empty:
                hourly_total = (merged['hours'] * merged['hourly_rate']).sum()
                total_hours = merged['hours'].sum()
    
    # Add retainer/flat fee income
    retainer_total = 0
    if not monthly_invoices.empty:
        retainer_total = monthly_invoices['amount'].sum()
    
    total_income = hourly_total + retainer_total
    
    work_days_list = settings['work_days'].split(',')
    total_work_days = get_work_days_in_month(year, month, work_days_list, non_work_days_df)
    
    # Calculate days worked so far
    today = datetime.now().date()
    days_worked = 0
    for day in range(1, min(today.day + 1, calendar.monthrange(year, month)[1] + 1)):
        date = datetime(year, month, day).date()
        if is_work_day(date, work_days_list, non_work_days_df) and date <= today:
            days_worked += 1
    
    daily_target = settings['monthly_target'] / total_work_days if total_work_days > 0 else 0
    target_so_far = daily_target * days_worked
    
    # Calculate average hourly rate from hourly clients
    avg_hourly_rate = 0
    if not clients_df.empty:
        hourly_clients = clients_df[clients_df['billing_type'] == 'Hourly']
        if not hourly_clients.empty:
            avg_hourly_rate = hourly_clients['hourly_rate'].mean()
    
    # Calculate target hours per day
    daily_hours_target = daily_target / avg_hourly_rate if avg_hourly_rate > 0 else 0
    
    return {
        'total_income': total_income,
        'hourly_income': hourly_total,
        'retainer_income': retainer_total,
        'monthly_target': settings['monthly_target'],
        'target_so_far': target_so_far,
        'daily_target': daily_target,
        'daily_hours_target': daily_hours_target,
        'total_work_days': total_work_days,
        'days_worked': days_worked,
        'total_hours': total_hours,
        'avg_hourly_rate': avg_hourly_rate
    }

def show_dashboard(clients_df, time_entries_df, invoices_df, settings, non_work_days_df):
    st.header("📊 Dashboard")
    
    # Month selector at the very top - start with current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Create month list starting from current month
    month_order = list(range(current_month, 13)) + list(range(1, current_month))
    month_labels = [calendar.month_name[m] for m in month_order]
    
    col1, col2 = st.columns(2)
    with col1:
        selected_month_label = st.selectbox("Month", month_labels, index=0)
        # Convert back to month number
        selected_month = month_order[month_labels.index(selected_month_label)]
    with col2:
        selected_year = st.selectbox("Year", range(2023, 2030), index=current_year - 2023)
    
    stats = calculate_monthly_stats(selected_year, selected_month, clients_df, time_entries_df, invoices_df, settings, non_work_days_df)
    
    st.markdown("---")
    
    # Top metrics - reorganized layout
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"${stats['total_income']:,.2f}")
        st.metric("Hourly Income", f"${stats['hourly_income']:,.2f}")
    with col2:
        st.metric("Monthly Target", f"${stats['monthly_target']:,.2f}")
        st.metric("Daily Income Target", f"${stats['daily_target']:,.2f}")
    with col3:
        st.metric("Work Days in Month", f"{stats['total_work_days']} days")
        st.metric("Retainer/Flat Fee Income", f"${stats['retainer_income']:,.2f}")
    
    # Progress chart
    st.markdown("---")
    st.subheader("Target vs Actuals")
    
    work_days_list = settings['work_days'].split(',')
    
    dates = []
    targets = []
    actuals = []
    cumulative_actual = 0
    cumulative_target = 0
    
    for day in range(1, calendar.monthrange(selected_year, selected_month)[1] + 1):
        date = datetime(selected_year, selected_month, day)
        dates.append(date)
        
        if is_work_day(date.date(), work_days_list, non_work_days_df):
            cumulative_target += stats['daily_target']
        
        targets.append(cumulative_target)
        
        # Calculate actual income up to this date (hourly only)
        if not time_entries_df.empty and not clients_df.empty:
            daily_entries = time_entries_df[time_entries_df['date'].dt.date == date.date()]
            if not daily_entries.empty:
                hourly_clients = clients_df[clients_df['billing_type'] == 'Hourly']
                if not hourly_clients.empty:
                    merged = daily_entries.merge(hourly_clients[['client_name', 'hourly_rate']], on='client_name', how='inner')
                    if not merged.empty:
                        daily_income = (merged['hours'] * merged['hourly_rate']).sum()
                        cumulative_actual += daily_income
        
        # Add retainer/flat fee income
        if not invoices_df.empty:
            daily_invoices = invoices_df[invoices_df['date'].dt.date == date.date()]
            if not daily_invoices.empty:
                cumulative_actual += daily_invoices['amount'].sum()
        
        actuals.append(cumulative_actual)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=targets, mode='lines', name='Target', line=dict(color='red', width=2)))
    fig.add_trace(go.Scatter(x=dates, y=actuals, mode='lines', name='Actuals', line=dict(color='blue', width=2)))
    
    # Add vertical line for today's date - use midnight to align with gridlines
    today = datetime.now()
    today_midnight = datetime(today.year, today.month, today.day)
    if datetime(selected_year, selected_month, 1) <= today <= datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1], 23, 59, 59):
        max_y = max(max(targets), max(actuals)) if actuals else max(targets)
        fig.add_trace(go.Scatter(
            x=[today_midnight, today_midnight],
            y=[0, max_y * 1.1],
            mode='lines',
            line=dict(color='green', width=2, dash='dash'),
            name='Today',
            showlegend=True
        ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode='x unified',
        height=400,
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            dtick=86400000  # 1 day in milliseconds
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray'
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Client Hour Limits Section
    st.markdown("---")
    st.subheader("⏱️ Client Hour Limits")
    
    if not clients_df.empty:
        # Filter for active clients with hour limits
        clients_with_limits = clients_df[(clients_df['has_hour_limit'] == True) & (clients_df['active'] == True)]
        
        if not clients_with_limits.empty:
            limit_data = []
            
            for _, client in clients_with_limits.iterrows():
                hours_used = calculate_client_hours(
                    client['client_name'], 
                    time_entries_df, 
                    client['limit_type'],
                    client['contract_start_date'],
                    selected_year,
                    selected_month
                )
                
                hours_remaining = client['hour_limit'] - hours_used
                percentage_used = (hours_used / client['hour_limit'] * 100) if client['hour_limit'] > 0 else 0
                
                # Determine status color
                if percentage_used >= 90:
                    status = "🔴 Critical"
                elif percentage_used >= 75:
                    status = "🟡 Warning"
                else:
                    status = "🟢 Good"
                
                limit_data.append({
                    'Client': client['client_name'],
                    'Limit Type': client['limit_type'],
                    'Total Limit': f"{client['hour_limit']:.1f} hrs",
                    'Hours Used': f"{hours_used:.1f} hrs",
                    'Hours Remaining': f"{hours_remaining:.1f} hrs",
                    'Usage %': f"{percentage_used:.1f}%",
                    'Status': status
                })
            
            if limit_data:
                limit_df = pd.DataFrame(limit_data)
                st.dataframe(limit_df, width='stretch', hide_index=True)
            else:
                st.info("No clients with hour limits have been used yet.")
        else:
            st.info("No clients have hour limits set. Configure limits in Client Management.")
    
    # Monthly breakdown
    st.markdown("---")
    st.subheader("Monthly Breakdown by Client")
    
    month_start = datetime(selected_year, selected_month, 1)
    month_end = datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
    
    # Create breakdown table
    breakdown_data = []
    
    # Hourly clients
    monthly_entries = time_entries_df[
        (time_entries_df['date'] >= month_start) & 
        (time_entries_df['date'] <= month_end)
    ] if not time_entries_df.empty else pd.DataFrame()
    
    if not monthly_entries.empty and not clients_df.empty:
        hourly_clients = clients_df[clients_df['billing_type'] == 'Hourly']
        if not hourly_clients.empty:
            hourly_breakdown = monthly_entries.groupby('client_name')['hours'].sum().reset_index()
            hourly_breakdown = hourly_breakdown.merge(hourly_clients[['client_name', 'hourly_rate']], on='client_name', how='inner')
            if not hourly_breakdown.empty:
                hourly_breakdown['total_invoice'] = hourly_breakdown['hours'] * hourly_breakdown['hourly_rate']
                hourly_breakdown['billing_type'] = 'Hourly'
                for _, row in hourly_breakdown.iterrows():
                    breakdown_data.append({
                        'Client': row['client_name'],
                        'Billing Type': 'Hourly',
                        'Hours': row['hours'],
                        'Rate': row['hourly_rate'],
                        'Total Invoice': row['total_invoice']
                    })
    
    # Retainer/Flat fee clients
    monthly_invoices = invoices_df[
        (invoices_df['date'] >= month_start) & 
        (invoices_df['date'] <= month_end)
    ] if not invoices_df.empty else pd.DataFrame()
    
    if not monthly_invoices.empty:
        retainer_breakdown = monthly_invoices.groupby('client_name')['amount'].sum().reset_index()
        for _, row in retainer_breakdown.iterrows():
            breakdown_data.append({
                'Client': row['client_name'],
                'Billing Type': 'Retainer/Flat Fee',
                'Hours': 0,
                'Rate': 0,
                'Total Invoice': row['amount']
            })
    
    if breakdown_data:
        breakdown_df = pd.DataFrame(breakdown_data)
        st.dataframe(breakdown_df.style.format({
            'Hours': '{:.2f}',
            'Rate': '${:.2f}',
            'Total Invoice': '${:.2f}'
        }), width='stretch')
        
        # Show totals
        st.markdown("---")
        total_invoice = breakdown_df['Total Invoice'].sum()
        st.markdown(f"**TOTAL INVOICE: ${total_invoice:,.2f}**")
    else:
        st.info("No billable activity for this month yet.")
    
    # Weekly breakdown
    st.markdown("---")
    st.subheader("Weekly Breakdown by Client")
    
    # Generate all weeks in the selected month
    month_start = datetime(selected_year, selected_month, 1)
    month_end = datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
    
    # Find all Monday-starting weeks that overlap with this month
    all_weeks = []
    current_date = month_start
    
    # Go back to the Monday of the first week
    while current_date.weekday() != 0:  # 0 = Monday
        current_date -= timedelta(days=1)
    
    # Collect all weeks that overlap with the month
    while current_date <= month_end:
        week_end = current_date + timedelta(days=6)
        # Only include weeks that have at least one day in the selected month
        if current_date <= month_end and week_end >= month_start:
            all_weeks.append(current_date)
        current_date += timedelta(days=7)
    
    # Get active clients
    if not clients_df.empty:
        active_clients = sorted(clients_df[clients_df['active'] == True]['client_name'].tolist())
    else:
        active_clients = []
    
    if active_clients and all_weeks:
        # Create pivot data structure - initialize with zeros for all clients and weeks
        pivot_data = {}
        for client_name in active_clients:
            pivot_data[client_name] = {week: 0 for week in all_weeks}
        
        # Fill in actual hours from time entries
        if not monthly_entries.empty:
            monthly_entries_copy = monthly_entries.copy()
            monthly_entries_copy['week_start'] = monthly_entries_copy['date'].dt.to_period('W').apply(lambda r: r.start_time)
            
            for client_name in monthly_entries_copy['client_name'].unique():
                if client_name in pivot_data:  # Only include active clients
                    client_entries = monthly_entries_copy[monthly_entries_copy['client_name'] == client_name]
                    
                    # Sum hours for each week
                    for week_start in all_weeks:
                        week_entries = client_entries[client_entries['week_start'] == week_start]
                        if not week_entries.empty:
                            pivot_data[client_name][week_start] = week_entries['hours'].sum()
        
        # Create column headers with week ranges
        week_columns = []
        for week_start in all_weeks:
            week_end = week_start + timedelta(days=6)
            # Adjust week end to stay within month bounds
            if week_end > month_end:
                week_end = month_end
            if week_start < month_start:
                display_start = month_start
            else:
                display_start = week_start
            week_columns.append(f"{display_start.strftime('%b %d')}-{week_end.strftime('%d')}")
        
        # Build rows
        table_rows = []
        for client_name in active_clients:
            row = {'Client': client_name}
            total_hours = 0
            
            for i, week_start in enumerate(all_weeks):
                hours = pivot_data[client_name][week_start]
                total_hours += hours
                # Display "-" for zero hours, otherwise show hours
                row[week_columns[i]] = f"{hours:.1f}" if hours > 0 else "-"
            
            row['Total'] = f"{total_hours:.1f}"
            table_rows.append(row)
        
        # Create DataFrame and display
        weekly_pivot_df = pd.DataFrame(table_rows)
        st.dataframe(weekly_pivot_df, use_container_width=True, hide_index=True)
    else:
        st.info("No active clients or weeks available.")

def show_calendar_manager(non_work_days_df, settings):
    st.header("📅 Work Calendar")
    
    # Month selector
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox("Select Month", range(1, 13), index=datetime.now().month - 1, format_func=lambda x: calendar.month_name[x], key='cal_month')
    with col2:
        selected_year = st.selectbox("Select Year", range(2023, 2030), index=datetime.now().year - 2023, key='cal_year')
    
    work_days_list = settings['work_days'].split(',')
    
    # Show work days count
    work_days_count = get_work_days_in_month(selected_year, selected_month, work_days_list, non_work_days_df)
    st.info(f"✅ **{work_days_count} work days** in {calendar.month_name[selected_month]} {selected_year}")
    
    st.markdown("---")
    st.markdown("""
    **Legend:**
    - 🟢 **Green** = Work Day
    - 🔴 **Red** = Weekend/Non-Work Day (from Settings)
    - ⚫ **Gray** = Holiday/Vacation (click to toggle)
    
    Click any work day to mark it as a holiday or vacation day.
    """)
    
    # Get month calendar
    cal = calendar.monthcalendar(selected_year, selected_month)
    
    # Display calendar
    st.markdown("### " + calendar.month_name[selected_month] + f" {selected_year}")
    
    # Day headers
    cols = st.columns(7)
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, col in enumerate(cols):
        col.markdown(f"**{day_names[i]}**")
    
    # Custom CSS for calendar styling
    st.markdown("""
    <style>
    .calendar-button {
        width: 100%;
        padding: 0.5rem 0.75rem;
        text-align: center;
        border-radius: 0.5rem;
        border: 1px solid;
        background-color: white !important;
        cursor: default;
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.6;
        margin: 0;
        box-sizing: border-box;
    }
    .work-day {
        color: #28a745;
        border-color: #28a745;
    }
    .holiday {
        color: #6c757d;
        border-color: #6c757d;
    }
    .non-work {
        color: #dc3545;
        border-color: #ddd;
        cursor: default;
    }
    /* Ensure all column divs have same styling */
    div[data-testid="column"] > div > div {
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Calendar grid with session state for clicks
    if 'calendar_click' not in st.session_state:
        st.session_state.calendar_click = None
    
    # Calendar grid
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date = datetime(selected_year, selected_month, day).date()
                day_name = calendar.day_name[date.weekday()]
                
                # Check if this is a regular work day
                is_regular_work_day = day_name in work_days_list
                
                # Check if this day is marked as non-work day (holiday/vacation)
                is_marked_non_work = False
                reason = ""
                if not non_work_days_df.empty:
                    day_record = non_work_days_df[non_work_days_df['date'] == date]
                    if not day_record.empty:
                        is_marked_non_work = True
                        reason = day_record.iloc[0]['reason']
                
                # Determine button appearance
                if not is_regular_work_day:
                    # Weekend or regular non-work day - red text on white background, not clickable
                    label = f"🔴 {day}"
                    cols[i].markdown(f"<div class='calendar-button non-work'>{label}</div>", unsafe_allow_html=True)
                elif is_marked_non_work:
                    # Marked as holiday/vacation - gray button, clickable
                    label = f"⚫ {day}"
                    # Use custom styling for white background
                    cols[i].markdown(f"""
                    <style>
                    button[key="day_{selected_year}_{selected_month}_{day}"] {{
                        background-color: white !important;
                        color: #6c757d !important;
                        border: 2px solid #6c757d !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    if cols[i].button(label, key=f"day_{selected_year}_{selected_month}_{day}", use_container_width=True):
                        # Remove from non-work days
                        non_work_days_df = non_work_days_df[non_work_days_df['date'] != date]
                        save_non_work_days(non_work_days_df)
                        st.rerun()
                else:
                    # Regular work day - green button, clickable
                    label = f"🟢 {day}"
                    # Use custom styling for white background
                    cols[i].markdown(f"""
                    <style>
                    button[key="day_{selected_year}_{selected_month}_{day}"] {{
                        background-color: white !important;
                        color: #28a745 !important;
                        border: 2px solid #28a745 !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    if cols[i].button(label, key=f"day_{selected_year}_{selected_month}_{day}", use_container_width=True):
                        # Add as non-work day
                        st.session_state[f'adding_non_work_{date}'] = True
                        st.rerun()
    
    # Handle adding non-work day with reason
    for key in list(st.session_state.keys()):
        if key.startswith('adding_non_work_'):
            date_str = key.replace('adding_non_work_', '')
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            with st.form(f"reason_form_{date}"):
                st.write(f"**Mark {date.strftime('%B %d, %Y')} as non-work day**")
                reason = st.text_input("Reason (e.g., Holiday, Vacation, Sick)", value="Holiday")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("Save", type="primary"):
                        new_row = pd.DataFrame({
                            'date': [date],
                            'reason': [reason]
                        })
                        updated_df = pd.concat([non_work_days_df, new_row], ignore_index=True)
                        save_non_work_days(updated_df)
                        del st.session_state[key]
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        del st.session_state[key]
                        st.rerun()
    
    # Show list of non-work days
    st.markdown("---")
    st.subheader("Holidays & Vacation Days This Month")
    
    month_start = datetime(selected_year, selected_month, 1).date()
    month_end = datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1]).date()
    
    if not non_work_days_df.empty:
        month_non_work = non_work_days_df[
            (non_work_days_df['date'] >= month_start) & 
            (non_work_days_df['date'] <= month_end)
        ].sort_values('date')
        
        if not month_non_work.empty:
            display_df = month_non_work.copy()
            display_df['date'] = display_df['date'].apply(lambda x: x.strftime('%B %d, %Y (%A)'))
            st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.info("No holidays or vacation days marked for this month.")
    else:
        st.info("No holidays or vacation days marked for this month.")

def show_time_entry(clients_df, time_entries_df):
    st.header("⏰ Time Entry")
    
    if clients_df.empty:
        st.warning("No clients available. Please add clients first in the Client Management page.")
        return
    
    # Show ALL active clients (both hourly and retainer/flat fee) - sorted alphabetically
    active_clients = sorted(clients_df[clients_df['active'] == True]['client_name'].tolist())
    
    if not active_clients:
        st.warning("No active clients. Please activate clients in Client Management.")
        return
    
    with st.form("time_entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Date", datetime.now())
            client = st.selectbox("Client", active_clients)
        with col2:
            hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=0.25, value=1.0)
            notes = st.text_area("Notes (optional)")
        
        # Show client billing info and check limits
        if client:
            client_info = clients_df[clients_df['client_name'] == client].iloc[0]
            if client_info['billing_type'] == 'Hourly':
                st.info(f"💵 Hourly client - Rate: ${client_info['hourly_rate']:.2f}/hr")
            else:
                st.info(f"📋 {client_info['billing_type']} client - Hours tracked for contract limits only (not billed)")
            
            # Check hour limits and warn if exceeded
            if client_info['has_hour_limit']:
                now = datetime.now()
                current_hours = calculate_client_hours(
                    client, 
                    time_entries_df, 
                    client_info['limit_type'],
                    client_info['contract_start_date'],
                    now.year,
                    now.month
                )
                
                hours_after = current_hours + hours
                if hours_after > client_info['hour_limit']:
                    hours_over = hours_after - client_info['hour_limit']
                    st.warning(f"⚠️ This will exceed the {client_info['limit_type']} limit by {hours_over:.1f} hours. Current: {current_hours:.1f}/{client_info['hour_limit']:.1f} hrs")
        
        submitted = st.form_submit_button("Add Entry")
        
        if submitted:
            new_entry = pd.DataFrame({
                'date': [pd.Timestamp(entry_date)],
                'client_name': [client],
                'hours': [hours],
                'notes': [notes]
            })
            updated_df = pd.concat([time_entries_df, new_entry], ignore_index=True)
            save_time_entries(updated_df)
            st.success(f"Added {hours} hours for {client} on {entry_date}")
            st.rerun()
    
    # Show recent entries with billing type indicator
    st.subheader("Recent Entries")
    if not time_entries_df.empty:
        recent = time_entries_df.sort_values('date', ascending=False).head(20).copy()
        recent['date'] = recent['date'].dt.strftime('%Y-%m-%d')
        
        # Add billing type and rate info
        if not clients_df.empty:
            recent = recent.merge(
                clients_df[['client_name', 'billing_type', 'hourly_rate']], 
                on='client_name', 
                how='left'
            )
            # Format billable as string to avoid type conflicts
            recent['billable'] = recent.apply(
                lambda row: f"${row['hours'] * row['hourly_rate']:.2f}" if row['billing_type'] == 'Hourly' else 'Not billed',
                axis=1
            )
            recent = recent[['date', 'client_name', 'hours', 'billing_type', 'billable', 'notes']]
            
            # Convert all to string to avoid Arrow issues
            display_recent = recent.copy()
            display_recent['hours'] = display_recent['hours'].apply(lambda x: f"{x:.2f}")
            display_recent = display_recent.astype(str)
            
            st.dataframe(display_recent, width='stretch', hide_index=True)
        else:
            st.dataframe(recent, width='stretch', hide_index=True)
    else:
        st.info("No time entries yet. Add your first entry above!")

def show_client_management(clients_df):
    st.header("👥 Client Management")
    
    tab1, tab2 = st.tabs(["Active Clients", "Add New Client"])
    
    with tab1:
        if not clients_df.empty:
            st.info("Edit client information below. Changes save automatically when you click outside the table.")
            
            # Editable view
            display_df = clients_df[['client_name', 'billing_type', 'hourly_rate', 'has_hour_limit', 'limit_type', 'hour_limit', 'active']].copy()
            
            edited_df = st.data_editor(
                display_df,
                hide_index=True,
                width='stretch',
                column_config={
                    "client_name": "Client Name",
                    "billing_type": st.column_config.SelectboxColumn("Billing Type", options=["Hourly", "Retainer/Flat Fee"]),
                    "hourly_rate": st.column_config.NumberColumn("Hourly Rate", format="$%.2f"),
                    "has_hour_limit": st.column_config.CheckboxColumn("Has Hour Limit"),
                    "limit_type": st.column_config.SelectboxColumn("Limit Type", options=["None", "Monthly", "Contract Total"]),
                    "hour_limit": st.column_config.NumberColumn("Hour Limit", format="%.1f"),
                    "active": st.column_config.CheckboxColumn("Active")
                },
                disabled=["client_name"]  # Don't allow changing client names
            )
            
            if st.button("💾 Save Changes"):
                # Merge changes back into full dataframe
                for col in edited_df.columns:
                    clients_df[col] = edited_df[col]
                save_clients(clients_df)
                st.success("Client changes saved!")
                st.rerun()
        else:
            st.info("No clients yet. Add your first client in the 'Add New Client' tab!")
    
    with tab2:
        st.subheader("Add New Client")
        
        with st.form("add_client_form"):
            st.write("### Step 1: Basic Information")
            client_name = st.text_input("Client Name *")
            
            col1, col2 = st.columns(2)
            with col1:
                billing_type = st.selectbox("Billing Type *", ["Hourly", "Retainer/Flat Fee"])
            with col2:
                if billing_type == "Hourly":
                    hourly_rate = st.number_input("Hourly Rate ($) *", min_value=0.0, step=10.0, value=100.0)
                else:
                    hourly_rate = 0.0
                    st.info("For retainer/flat fee clients, payments are tracked in Invoices.")
            
            st.markdown("---")
            st.write("### Step 2: Hour Limits (Optional)")
            has_hour_limit = st.checkbox("This client has an hour limit")
            
            limit_type = st.selectbox(
                "Limit Type", 
                ["Monthly", "Contract Total"],
                help="Monthly: Resets each month. Contract Total: Total hours for entire contract."
            )
            
            hour_limit = st.number_input(
                "Hour Limit", 
                min_value=0.0, 
                step=1.0, 
                value=40.0,
                help="Enter the maximum number of hours for this client"
            )
            
            contract_start_date = st.date_input(
                "Contract Start Date (required for Contract Total)", 
                value=datetime.now(),
                help="Required when Limit Type is 'Contract Total'"
            )
            
            st.caption("⚠️ If you check 'hour limit' and select 'Contract Total', the start date above is required.")
            
            submitted = st.form_submit_button("Add Client", type="primary")
            
            if submitted:
                # Validation
                if not client_name:
                    st.error("Please enter a client name")
                elif client_name in clients_df['client_name'].values:
                    st.error(f"Client '{client_name}' already exists!")
                elif has_hour_limit and hour_limit <= 0:
                    st.error("Please enter a valid hour limit greater than 0")
                elif has_hour_limit and limit_type == "Contract Total" and not contract_start_date:
                    st.error("Please enter a contract start date for Contract Total limit type")
                else:
                    # Save the client
                    final_start_date = contract_start_date.strftime('%Y-%m-%d')
                    
                    new_client = pd.DataFrame({
                        'client_name': [client_name],
                        'hourly_rate': [float(hourly_rate)],
                        'billing_type': [billing_type],
                        'active': [True],
                        'has_hour_limit': [has_hour_limit],
                        'limit_type': [limit_type if has_hour_limit else 'None'],
                        'hour_limit': [float(hour_limit) if has_hour_limit else 0.0],
                        'contract_start_date': [final_start_date]
                    })
                    
                    updated_df = pd.concat([clients_df, new_client], ignore_index=True)
                    save_clients(updated_df)
                    st.success(f"✅ Added client: {client_name}")
                    st.rerun()

def show_invoices(invoices_df, clients_df):
    st.header("💰 Retainer & Flat Fee Income")
    st.info("Use this page to record payments from retainer and flat fee clients.")
    
    # Get list of clients for dropdown - sorted alphabetically
    if clients_df.empty:
        st.warning("No clients available. Please add clients first in the Client Management page.")
        return
    
    client_names = sorted(clients_df['client_name'].tolist())
    
    with st.form("invoice_form"):
        col1, col2 = st.columns(2)
        with col1:
            invoice_date = st.date_input("Date", datetime.now())
            client_name = st.selectbox("Client", client_names)
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.0, step=100.0)
            income_type = st.selectbox("Type", ["Retainer", "Flat Fee", "Bonus", "Other"])
        
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Add Income")
        
        if submitted:
            if client_name and amount > 0:
                new_invoice = pd.DataFrame({
                    'date': [pd.Timestamp(invoice_date)],
                    'client_name': [client_name],
                    'amount': [amount],
                    'type': [income_type],
                    'description': [description]
                })
                updated_df = pd.concat([invoices_df, new_invoice], ignore_index=True)
                save_invoices(updated_df)
                st.success(f"Added ${amount} income from {client_name}")
                st.rerun()
            else:
                st.error("Please select a client and enter an amount")
    
    st.subheader("Recent Income")
    if not invoices_df.empty:
        recent = invoices_df.sort_values('date', ascending=False).head(20).copy()
        recent['date'] = recent['date'].dt.strftime('%Y-%m-%d')
        st.dataframe(recent.style.format({'amount': '${:.2f}'}), width='stretch')
    else:
        st.info("No retainer/flat fee income recorded yet.")

def show_settings(settings):
    st.header("⚙️ Settings")
    
    monthly_target = st.number_input("Monthly Income Target ($)", min_value=0.0, step=1000.0, value=float(settings['monthly_target']))
    
    current_work_days = settings['work_days'].split(',') if isinstance(settings['work_days'], str) else ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    work_days = st.multiselect(
        "Regular Work Days (use Calendar page to mark specific holidays/vacation days)",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        default=current_work_days
    )
    
    if st.button("Save Settings"):
        if work_days:
            save_settings(monthly_target, work_days)
            st.success("Settings saved!")
            st.rerun()
        else:
            st.error("Please select at least one work day")

def show_scenario_planning(clients_df, time_entries_df, invoices_df, settings, non_work_days_df):
    st.header("🔮 Scenario Planning")
    st.info("Plan future work hours and see how they affect your monthly income. Changes here are NOT saved to your actual time entries.")
    
    # Month selector
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1, format_func=lambda x: calendar.month_name[x], key="scenario_month")
    with col2:
        selected_year = st.selectbox("Year", range(2023, 2030), index=datetime.now().year - 2023, key="scenario_year")
    
    # Initialize scenario entries in session state
    if 'scenario_entries' not in st.session_state:
        st.session_state.scenario_entries = []
    
    # Get active hourly clients
    active_hourly_clients = sorted(clients_df[(clients_df['active'] == True) & (clients_df['billing_type'] == 'Hourly')]['client_name'].tolist())
    
    if not active_hourly_clients:
        st.warning("No active hourly clients to plan for.")
        return
    
    # Quick entry form
    st.subheader("Add Scenario Hours")
    with st.form("scenario_entry_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            scenario_date = st.date_input("Date", datetime.now(), key="scenario_date")
        with col2:
            scenario_client = st.selectbox("Client", active_hourly_clients, key="scenario_client")
        with col3:
            scenario_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=0.5, value=4.0, key="scenario_hours")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Add to Scenario", type="primary"):
                st.session_state.scenario_entries.append({
                    'date': pd.Timestamp(scenario_date),
                    'client_name': scenario_client,
                    'hours': scenario_hours
                })
                st.success(f"Added {scenario_hours} hours for {scenario_client}")
                st.rerun()
        with col2:
            if st.form_submit_button("Clear All Scenarios"):
                st.session_state.scenario_entries = []
                st.success("Cleared all scenario entries")
                st.rerun()
    
    # Show current scenario entries
    if st.session_state.scenario_entries:
        st.subheader("Current Scenario Entries")
        scenario_df = pd.DataFrame(st.session_state.scenario_entries)
        scenario_df['date_str'] = scenario_df['date'].dt.strftime('%Y-%m-%d')
        display_scenario = scenario_df[['date_str', 'client_name', 'hours']].copy()
        display_scenario.columns = ['Date', 'Client', 'Hours']
        st.dataframe(display_scenario, width='stretch', hide_index=True)
    
    # Combine actual and scenario data
    combined_entries = pd.concat([time_entries_df, pd.DataFrame(st.session_state.scenario_entries)], ignore_index=True) if st.session_state.scenario_entries else time_entries_df
    
    # Calculate stats with combined data
    stats = calculate_monthly_stats(selected_year, selected_month, clients_df, combined_entries, invoices_df, settings, non_work_days_df)
    
    # Show metrics
    st.markdown("---")
    st.subheader("Scenario Results")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Projected Total Income", f"${stats['total_income']:,.2f}")
    with col2:
        st.metric("Monthly Target", f"${stats['monthly_target']:,.2f}")
    with col3:
        difference = stats['total_income'] - stats['monthly_target']
        st.metric("vs Target", f"${difference:,.2f}", delta=f"${difference:,.2f}")
    
    # Client Hour Limits with Scenario
    st.markdown("---")
    st.subheader("⏱️ Client Hour Limits (with Scenario)")
    
    if not clients_df.empty:
        # Filter for active clients with hour limits
        clients_with_limits = clients_df[(clients_df['has_hour_limit'] == True) & (clients_df['active'] == True)]
        
        if not clients_with_limits.empty:
            limit_data = []
            
            for _, client in clients_with_limits.iterrows():
                # Calculate hours with scenario data
                hours_used = calculate_client_hours(
                    client['client_name'], 
                    combined_entries,  # Use combined entries including scenarios
                    client['limit_type'],
                    client['contract_start_date'],
                    selected_year,
                    selected_month
                )
                
                hours_remaining = client['hour_limit'] - hours_used
                percentage_used = (hours_used / client['hour_limit'] * 100) if client['hour_limit'] > 0 else 0
                
                # Determine status color
                if percentage_used >= 90:
                    status = "🔴 Critical"
                elif percentage_used >= 75:
                    status = "🟡 Warning"
                else:
                    status = "🟢 Good"
                
                limit_data.append({
                    'Client': client['client_name'],
                    'Limit Type': client['limit_type'],
                    'Total Limit': f"{client['hour_limit']:.1f} hrs",
                    'Hours Used': f"{hours_used:.1f} hrs",
                    'Hours Remaining': f"{hours_remaining:.1f} hrs",
                    'Usage %': f"{percentage_used:.1f}%",
                    'Status': status
                })
            
            if limit_data:
                limit_df = pd.DataFrame(limit_data)
                st.dataframe(limit_df, width='stretch', hide_index=True)
            else:
                st.info("No clients with hour limits have been used yet.")
        else:
            st.info("No clients have hour limits set.")
    
    # Generate plot with scenario data
    st.markdown("---")
    st.subheader("Target vs Actuals (with Scenario)")
    
    work_days_list = settings['work_days'].split(',')
    
    dates = []
    targets = []
    actuals = []
    cumulative_actual = 0
    cumulative_target = 0
    
    for day in range(1, calendar.monthrange(selected_year, selected_month)[1] + 1):
        date = datetime(selected_year, selected_month, day)
        dates.append(date)
        
        if is_work_day(date.date(), work_days_list, non_work_days_df):
            cumulative_target += stats['daily_target']
        
        targets.append(cumulative_target)
        
        # Calculate actual income up to this date (hourly only)
        if not combined_entries.empty and not clients_df.empty:
            daily_entries = combined_entries[combined_entries['date'].dt.date == date.date()]
            if not daily_entries.empty:
                hourly_clients = clients_df[clients_df['billing_type'] == 'Hourly']
                if not hourly_clients.empty:
                    merged = daily_entries.merge(hourly_clients[['client_name', 'hourly_rate']], on='client_name', how='inner')
                    if not merged.empty:
                        daily_income = (merged['hours'] * merged['hourly_rate']).sum()
                        cumulative_actual += daily_income
        
        # Add retainer/flat fee income
        if not invoices_df.empty:
            daily_invoices = invoices_df[invoices_df['date'].dt.date == date.date()]
            if not daily_invoices.empty:
                cumulative_actual += daily_invoices['amount'].sum()
        
        actuals.append(cumulative_actual)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=targets, mode='lines', name='Target', line=dict(color='red', width=2)))
    fig.add_trace(go.Scatter(x=dates, y=actuals, mode='lines', name='Actuals + Scenario', line=dict(color='blue', width=2)))
    
    # Add vertical line for today's date
    today = datetime.now()
    today_midnight = datetime(today.year, today.month, today.day)
    if datetime(selected_year, selected_month, 1) <= today <= datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1], 23, 59, 59):
        max_y = max(max(targets), max(actuals)) if actuals else max(targets)
        fig.add_trace(go.Scatter(
            x=[today_midnight, today_midnight],
            y=[0, max_y * 1.1],
            mode='lines',
            line=dict(color='green', width=2, dash='dash'),
            name='Today',
            showlegend=True
        ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode='x unified',
        height=400,
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            dtick=86400000
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray'
        )
    )
    
    st.plotly_chart(fig, width='stretch')

# Main app
def main():
    st.set_page_config(page_title="Freelance Time Tracker", layout="wide")
    
    st.title("💼 Freelance Time Tracker")
    
    # Initialize files
    initialize_files()
    
    # Load data
    clients_df = load_clients()
    time_entries_df = load_time_entries()
    invoices_df = load_invoices()
    settings = load_settings()
    non_work_days_df = load_non_work_days()
    
    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Dashboard", "Calendar", "Time Entry", "Client Management", "Invoices", "Scenario Planning", "Settings"])
    
    if page == "Dashboard":
        show_dashboard(clients_df, time_entries_df, invoices_df, settings, non_work_days_df)
    elif page == "Calendar":
        show_calendar_manager(non_work_days_df, settings)
    elif page == "Time Entry":
        show_time_entry(clients_df, time_entries_df)
    elif page == "Client Management":
        show_client_management(clients_df)
    elif page == "Invoices":
        show_invoices(invoices_df, clients_df)
    elif page == "Scenario Planning":
        show_scenario_planning(clients_df, time_entries_df, invoices_df, settings, non_work_days_df)
    elif page == "Settings":
        show_settings(settings)

if __name__ == "__main__":
    main()