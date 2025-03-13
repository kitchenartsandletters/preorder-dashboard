"""
Preorder Approvals Management Page for the Admin Dashboard.

This module provides the interface for managing preorder approvals.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Initialize data service
from data.data_service import DataService

def show_approvals():
    """
    Display the preorder approvals management page.
    """
    # Initialize data service with test mode from session state
    test_mode = st.session_state.get('test_mode', False)
    data_service = DataService(test_mode=test_mode)
    
    st.subheader("Preorder Approval Management")
    
    # Create tabs for different approval functions
    tabs = st.tabs(["Active Approvals", "Pending Releases", "Approval History"])
    
    # Active Approvals Tab
    with tabs[0]:
        st.subheader("Current Approval Issues")
        
        with st.spinner("Loading approval data..."):
            # Get approval issues from GitHub
            approval_issues = data_service.get_approval_status()
            
            # Get pending releases
            pending_releases = data_service.get_pending_releases()
        
        # Filter for open issues
        open_issues = [issue for issue in approval_issues if issue['status'] == 'open']
        
        if open_issues:
            # Display each open issue
            for issue in open_issues:
                with st.expander(f"{issue['title']} (#{issue['issue_number']})", expanded=True):
                    # Display issue details
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Issue Number:** #{issue['issue_number']}")
                        st.markdown(f"**Created:** {issue['created_at'][:10]}")
                        st.markdown(f"**Status:** {issue['status'].capitalize()}")
                        
                        # Count approved ISBNs
                        approved_count = len(issue['approved_isbns'])
                        st.markdown(f"**Approved ISBNs:** {approved_count}")
                    
                    with col2:
                        # Add action buttons
                        st.markdown("**Actions:**")
                        
                        # Link to GitHub issue
                        st.markdown(f"[View on GitHub]({issue['url']})")
                        
                        # Process button (would close the issue in a real implementation)
                        if st.button("Process Approvals", key=f"process_{issue['issue_number']}"):
                            st.success("Processing approvals... (This would execute the approval process in a real implementation)")
                        
                        # Close button (would just close without processing)
                        if st.button("Close Issue", key=f"close_{issue['issue_number']}"):
                            st.warning("Closing issue without processing...")
                    
                    # Display approved ISBNs if any
                    if issue['approved_isbns']:
                        st.subheader("Approved ISBNs")
                        
                        # Create a table with ISBN and title if available
                        approved_data = []
                        
                        for isbn in issue['approved_isbns']:
                            # Try to find title in pending releases
                            title = "Unknown"
                            quantity = 0
                            pub_date = "Unknown"
                            
                            for release in pending_releases.get('pending_releases', []):
                                if release.get('isbn') == isbn:
                                    title = release.get('title', 'Unknown')
                                    quantity = release.get('quantity', 0)
                                    pub_date = release.get('original_pub_date', 'Unknown')
                                    break
                            
                            approved_data.append({
                                'ISBN': isbn,
                                'Title': title,
                                'Quantity': quantity,
                                'Publication Date': pub_date
                            })
                        
                        # Display as DataFrame
                        approved_df = pd.DataFrame(approved_data)
                        st.dataframe(approved_df, use_container_width=True)
        else:
            st.info("No open approval issues found.")
            
            # Option to create a new approval issue
            if st.button("Create New Approval Issue"):
                st.warning("This would create a new approval issue in GitHub.")
                st.info("Feature not yet implemented in this dashboard.")
    
    # Pending Releases Tab
    with tabs[1]:
        st.subheader("Books Ready for Release")
        
        # Get pending releases data
        pending_items = pending_releases.get('pending_releases', [])
        
        if pending_items:
            # Create a DataFrame for the pending releases
            pending_df = pd.DataFrame(pending_items)
            
            # Add a selection column
            pending_df['Selected'] = False
            
            # Display the pending releases with checkboxes
            edited_df = st.data_editor(
                pending_df,
                hide_index=True,
                column_config={
                    "Selected": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select for approval",
                        default=False,
                    ),
                    "isbn": st.column_config.TextColumn(
                        "ISBN",
                        width="medium",
                        help="Book ISBN",
                    ),
                    "title": st.column_config.TextColumn(
                        "Title",
                        width="large",
                    ),
                    "quantity": st.column_config.NumberColumn(
                        "Quantity",
                        help="Pre-ordered quantity",
                    ),
                    "original_pub_date": st.column_config.DateColumn(
                        "Publication Date",
                        format="YYYY-MM-DD",
                        help="Original publication date",
                    ),
                    "overridden_pub_date": st.column_config.DateColumn(
                        "Override Date",
                        format="YYYY-MM-DD",
                        help="Overridden publication date (if any)",
                    ),
                },
                use_container_width=True,
            )
            
            # Count selected items
            selected_count = edited_df['Selected'].sum()
            
            # Display approval options
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"Selected {selected_count} of {len(pending_items)} pending books")
                
                # Create approval issue button
                if st.button("Create Approval Issue for Selected"):
                    if selected_count > 0:
                        # This would create a GitHub issue with the selected books
                        st.success(f"Creating approval issue for {selected_count} books...")
                        
                        # Get selected ISBNs
                        selected_isbns = edited_df[edited_df['Selected']]['isbn'].tolist()
                        
                        # Show the ISBNs that would be included
                        st.code("\n".join(selected_isbns))
                        
                        st.info("Feature not fully implemented - would create GitHub issue")
                    else:
                        st.error("Please select at least one book to approve")
            
            with col2:
                # Option to approve directly without GitHub
                if st.button("Approve Selected Directly"):
                    if selected_count > 0:
                        st.success(f"Directly approving {selected_count} books...")
                        
                        # Get selected ISBNs
                        selected_isbns = edited_df[edited_df['Selected']]['isbn'].tolist()
                        
                        # Show the ISBNs that would be approved
                        st.code("\n".join(selected_isbns))
                        
                        st.info("Feature not fully implemented - would process approvals")
                    else:
                        st.error("Please select at least one book to approve")
        else:
            st.info("No pending releases found at this time.")
            
            # Add refresh button
            if st.button("Refresh Data"):
                st.experimental_rerun()
    
    # Approval History Tab
    with tabs[2]:
        st.subheader("Approval History")
        
        # Filter for closed issues
        closed_issues = [issue for issue in approval_issues if issue['status'] == 'closed']
        
        if closed_issues:
            # Sort by creation date (most recent first)
            closed_issues.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Display as a table
            history_data = []
            for issue in closed_issues:
                history_data.append({
                    'Issue Number': issue['issue_number'],
                    'Title': issue['title'],
                    'Created Date': issue['created_at'][:10],
                    'Approved ISBNs': len(issue['approved_isbns']),
                    'GitHub URL': issue['url']
                })
            
            history_df = pd.DataFrame(history_data)
            
            # Create a custom column config with a link formatter
            st.dataframe(
                history_df,
                column_config={
                    'GitHub URL': st.column_config.LinkColumn(),
                },
                use_container_width=True
            )
            
            # Show approval statistics
            if len(history_data) > 0:
                # Calculate total approved ISBNs
                total_approved = sum(issue['Approved ISBNs'] for issue in history_data)
                avg_approved = total_approved / len(history_data)
                
                st.markdown(f"**Total approval issues:** {len(history_data)}")
                st.markdown(f"**Total approved ISBNs:** {total_approved}")
                st.markdown(f"**Average ISBNs per issue:** {avg_approved:.1f}")
                
                # Create a bar chart of approvals over time
                # Group by month
                history_df['Month'] = pd.to_datetime(history_df['Created Date']).dt.strftime('%Y-%m')
                monthly_approvals = history_df.groupby('Month').agg({
                    'Issue Number': 'count',
                    'Approved ISBNs': 'sum'
                }).reset_index()
                
                # Rename columns
                monthly_approvals = monthly_approvals.rename(columns={
                    'Issue Number': 'Issues'
                })
                
                # Create the chart
                fig = px.bar(
                    monthly_approvals,
                    x='Month',
                    y='Approved ISBNs',
                    title='Monthly Approval History',
                    labels={'Approved ISBNs': 'Books Approved', 'Month': 'Month'}
                )
                
                # Add issue count as a line
                fig.add_trace(
                    go.Scatter(
                        x=monthly_approvals['Month'],
                        y=monthly_approvals['Issues'],
                        mode='lines+markers',
                        name='Approval Issues',
                        yaxis='y2'
                    )
                )
                
                # Update layout for dual y-axis
                fig.update_layout(
                    yaxis2=dict(
                        title='Issue Count',
                        overlaying='y',
                        side='right'
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No closed approval issues found in the history.")