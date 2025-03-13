"""
Main Dashboard Page for the Preorder Admin Dashboard.

This module provides the main dashboard view with key metrics and summaries.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Initialize data service
from data.data_service import DataService

def show_dashboard():
    """
    Display the main dashboard page with key metrics and summaries.
    """
    # Initialize data service with test mode from session state
    test_mode = st.session_state.get('test_mode', False)
    data_service = DataService(test_mode=test_mode)
    
    # Add loading state
    with st.spinner("Loading dashboard data..."):
        # Get required data
        preorder_products = data_service.get_preorder_products()
        pending_releases = data_service.get_pending_releases()
        preorder_tracking = data_service.get_preorder_tracking_data()
        approval_status = data_service.get_approval_status()
    
    # Display KPI cards
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Active Preorders",
            value=len(preorder_products),
            delta=None
        )
        
    # Publication Date Issues
    st.subheader("Publication Date Status")
    
    # Calculate statistics about publication dates
    future_pub_dates = 0
    past_pub_dates = 0
    missing_pub_dates = 0
    malformed_pub_dates = 0
    today = datetime.now().date()
    
    for product in preorder_products:
        pub_date_str = product.get('pub_date')
        
        if not pub_date_str:
            missing_pub_dates += 1
            continue
            
        try:
            pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
            
            if pub_date > today:
                future_pub_dates += 1
            else:
                past_pub_dates += 1
                
        except ValueError:
            malformed_pub_dates += 1
    
    # Create a bar chart for publication date status
    pub_date_data = {
        'Status': ['Future Dates', 'Past Dates', 'Missing Dates', 'Malformed Dates'],
        'Count': [future_pub_dates, past_pub_dates, missing_pub_dates, malformed_pub_dates]
    }
    pub_date_df = pd.DataFrame(pub_date_data)
    
    # Add a color scale based on severity (red for issues, green for good)
    color_scale = ['#2e7d32', '#c62828', '#c62828', '#c62828']  # Green for future (good), red for issues
    
    # Create bar chart using Plotly
    fig = px.bar(
        pub_date_df, 
        x='Status', 
        y='Count',
        title='Publication Date Status',
        color='Status',
        color_discrete_sequence=color_scale
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display warning if there are issues
    if past_pub_dates > 0 or missing_pub_dates > 0 or malformed_pub_dates > 0:
        st.warning(f"Found {past_pub_dates} past dates, {missing_pub_dates} missing dates, and {malformed_pub_dates} malformed dates that require attention.")
        
    # Display two columns for pending releases and recent approvals
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pending Releases")
        pending_items = pending_releases.get('pending_releases', [])
        
        if pending_items:
            # Create a DataFrame for display
            pending_df = pd.DataFrame(pending_items)
            
            # Rename columns for better display
            if 'original_pub_date' in pending_df.columns:
                pending_df = pending_df.rename(columns={
                    'original_pub_date': 'Original Date',
                    'overridden_pub_date': 'Override Date'
                })
            
            # Select columns to display
            display_cols = ['isbn', 'title', 'quantity', 'Original Date', 'Override Date']
            display_cols = [col for col in display_cols if col in pending_df.columns]
            
            # Style the DataFrame
            st.dataframe(
                pending_df[display_cols],
                use_container_width=True,
                height=300
            )
            
            # Add a button to go to approvals page
            if st.button("Go to Approvals Page"):
                st.session_state.current_page = "approvals"
                st.experimental_rerun()
        else:
            st.info("No pending releases found.")
    
    with col2:
        st.subheader("Recent Approvals")
        
        # Filter to just the most recent open approval issue
        open_approval_issues = [issue for issue in approval_status if issue['status'] == 'open']
        
        if open_approval_issues:
            # Sort by creation date (most recent first)
            open_approval_issues.sort(key=lambda x: x['created_at'], reverse=True)
            latest_issue = open_approval_issues[0]
            
            # Display issue information
            st.markdown(f"**Issue:** {latest_issue['title']}")
            st.markdown(f"**Created:** {latest_issue['created_at'][:10]}")
            st.markdown(f"**Approved ISBNs:** {len(latest_issue['approved_isbns'])}")
            
            # Display a link to the GitHub issue
            st.markdown(f"[View on GitHub]({latest_issue['url']})")
            
            # Display approved ISBNs in a table if any exist
            if latest_issue['approved_isbns']:
                # Create DataFrame from approved ISBNs
                approved_df = pd.DataFrame({
                    'ISBN': latest_issue['approved_isbns']
                })
                
                # Try to match with title information from pending releases
                if pending_items:
                    isbn_to_title = {item['isbn']: item['title'] for item in pending_items}
                    approved_df['Title'] = approved_df['ISBN'].map(isbn_to_title)
                
                st.dataframe(approved_df, use_container_width=True, height=200)
        else:
            st.info("No open approval issues found.")
    
    # Display preorder tracking summary
    st.subheader("Preorder Tracking")
    
    if isinstance(preorder_tracking, pd.DataFrame) and not preorder_tracking.empty:
        # Group by ISBN and sum quantities
        if 'ISBN' in preorder_tracking.columns and 'Quantity' in preorder_tracking.columns:
            isbn_summary = preorder_tracking.groupby('ISBN').agg({
                'Title': 'first',  # Take the first title for each ISBN
                'Quantity': 'sum',  # Sum the quantities
                'Pub Date': 'first'  # Take the first publication date
            }).reset_index()
            
            # Sort by quantity (descending)
            isbn_summary = isbn_summary.sort_values('Quantity', ascending=False)
            
            # Take top 10 for display
            top_isbns = isbn_summary.head(10)
            
            # Create a horizontal bar chart
            fig = px.bar(
                top_isbns,
                y='Title',
                x='Quantity',
                title='Top 10 Preordered Titles',
                orientation='h',
                color='Quantity',
                color_continuous_scale='Blues'
            )
            
            # Update layout for better display
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="Copies Preordered",
                yaxis_title=None
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show full table with a toggle
            if st.checkbox("Show Full Preorder Summary Table"):
                st.dataframe(isbn_summary, use_container_width=True)
        else:
            st.warning("Preorder tracking data is missing required columns.")
    else:
        st.info("No preorder tracking data available.")
        
    with col2:
        pending_count = pending_releases.get('total_pending_books', 0)
        st.metric(
            label="Pending Releases",
            value=pending_count,
            delta=None
        )
    
    with col3:
        if isinstance(preorder_tracking, pd.DataFrame) and not preorder_tracking.empty:
            total_preorder_quantity = preorder_tracking['Quantity'].sum()
            st.metric(
                label="Total Preorder Copies",
                value=f"{total_preorder_quantity:,}",
                delta=None
            )
        else:
            st.metric(
                label="Total Preorder Copies",
                value="0",
                delta=None
            )
    
    with col4:
        # Count open approval issues
        open_approvals = sum(1 for issue in approval_status if issue['status'] == 'open')
        st.metric(
            label="Open Approval Issues",
            value=open_approvals,
            delta=None
        )