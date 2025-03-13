"""
Sales Reports Page for the Preorder Admin Dashboard.

This module provides reporting functionality for preorder sales and status changes.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64

# Initialize data service
from data.data_service import DataService

def show_reports():
    """
    Display the sales reports page.
    """
    # Initialize data service with test mode from session state
    test_mode = st.session_state.get('test_mode', False)
    data_service = DataService(test_mode=test_mode)
    
    st.subheader("Preorder Sales Reports")
    
    # Create tabs for different report types
    tabs = st.tabs([
        "Weekly Sales Report", 
        "Publication Date Analysis", 
        "Status Changes",
        "Custom Report Builder"
    ])
    
    # Weekly Sales Report Tab
    with tabs[0]:
        st.subheader("Weekly Sales Report")
        
        # Select report date range
        col1, col2 = st.columns(2)
        
        with col1:
            # Default to last completed week (Sunday through Saturday)
            today = datetime.now().date()
            days_since_sunday = (today.weekday() + 1) % 7  # 0 = Sunday, 6 = Saturday
            last_saturday = today - timedelta(days=days_since_sunday + 1)
            last_sunday = last_saturday - timedelta(days=6)
            
            start_date = st.date_input(
                "Start Date",
                value=last_sunday,
                max_value=today
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=last_saturday,
                max_value=today
            )
        
        # Validate date range
        if start_date > end_date:
            st.error("Start date must be before end date")
        else:
            # Format date range for display
            date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            st.markdown(f"**Report Period:** {date_range}")
            
            # Generate report button
            if st.button("Generate Weekly Report"):
                with st.spinner("Generating report..."):
                    # In a real implementation, this would call the weekly report generation logic
                    
                    # For now, we'll simulate the report generation
                    if test_mode:
                        # Generate test data
                        report_data = generate_test_weekly_report(start_date, end_date)
                        
                        if report_data:
                            # Display report summary
                            st.success("Report generated successfully!")
                            
                            # Calculate summary statistics
                            total_sales = sum(item['Quantity'] for item in report_data)
                            unique_isbns = len(set(item['ISBN'] for item in report_data))
                            
                            # Display summary
                            st.metric("Total Books Sold", f"{total_sales:,}")
                            st.metric("Unique ISBNs", unique_isbns)
                            
                            # Convert to DataFrame
                            report_df = pd.DataFrame(report_data)
                            
                            # Display the report data
                            st.dataframe(report_df, use_container_width=True)
                            
                            # Create download buttons
                            csv = report_df.to_csv(index=False)
                            
                            # Create download buttons for different formats
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"weekly_report_{start_date}_to_{end_date}.csv",
                                    mime="text/csv"
                                )
                            
                            with col2:
                                # Excel export
                                buffer = io.BytesIO()
                                report_df.to_excel(buffer, index=False, engine='openpyxl')
                                buffer.seek(0)
                                
                                st.download_button(
                                    label="Download Excel",
                                    data=buffer,
                                    file_name=f"weekly_report_{start_date}_to_{end_date}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    else:
                        st.warning("This feature requires API access. Enable test mode to see sample data.")
    
    # Publication Date Analysis Tab
    with tabs[1]:
        st.subheader("Publication Date Analysis")
        
        with st.spinner("Loading publication date data..."):
            # Get preorder products
            preorder_products = data_service.get_preorder_products()
            
            # Get publication date overrides
            overrides = data_service.get_pub_date_overrides()
        
        if preorder_products:
            # Process publication dates
            pub_date_data = []
            today = datetime.now().date()
            
            for product in preorder_products:
                # Get barcode/ISBN
                barcode = product.get('barcode')
                
                # Skip products without barcode
                if not barcode:
                    continue
                
                # Check for override
                if barcode in overrides:
                    pub_date_str = overrides[barcode]
                    has_override = True
                else:
                    pub_date_str = product.get('pub_date')
                    has_override = False
                
                # Parse publication date
                try:
                    if pub_date_str:
                        pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
                        days_until = (pub_date - today).days
                        status = "Future" if days_until >= 0 else "Past"
                    else:
                        pub_date = None
                        days_until = None
                        status = "Missing"
                except ValueError:
                    pub_date = None
                    days_until = None
                    status = "Malformed"
                
                # Add to publication date data
                pub_date_data.append({
                    'ISBN': barcode,
                    'Title': product.get('title'),
                    'Publication Date': pub_date_str,
                    'Date Object': pub_date,
                    'Days Until Publication': days_until,
                    'Status': status,
                    'Has Override': has_override
                })
            
            # Convert to DataFrame
            pub_df = pd.DataFrame(pub_date_data)
            
            # Calculate statistics
            future_count = len(pub_df[pub_df['Status'] == 'Future'])
            past_count = len(pub_df[pub_df['Status'] == 'Past'])
            missing_count = len(pub_df[pub_df['Status'] == 'Missing'])
            malformed_count = len(pub_df[pub_df['Status'] == 'Malformed'])
            override_count = len(pub_df[pub_df['Has Override']])
            
            # Display statistics
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Future Dates", future_count)
            col2.metric("Past Dates", past_count)
            col3.metric("Missing Dates", missing_count)
            col4.metric("Malformed Dates", malformed_count)
            col5.metric("With Overrides", override_count)
            
            # Filter valid dates for timeline analysis
            valid_dates = pub_df[pub_df['Date Object'].notna()].copy()
            
            if not valid_dates.empty:
                # Group by month
                valid_dates['Publication Month'] = valid_dates['Date Object'].apply(
                    lambda x: x.strftime('%Y-%m') if x else None
                )
                
                # Filter out any None values that might have slipped through
                valid_dates = valid_dates.dropna(subset=['Publication Month'])
                
                if not valid_dates.empty:
                    monthly_counts = valid_dates.groupby('Publication Month').size().reset_index(name='Count')
                    
                    # Sort by month
                    monthly_counts = monthly_counts.sort_values('Publication Month')
                    
                    # Create a bar chart
                    fig = px.bar(
                        monthly_counts,
                        x='Publication Month',
                        y='Count',
                        title='Publication Dates by Month',
                        labels={'Count': 'Number of Books', 'Publication Month': 'Month'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Create a histogram of days until publication
                future_pubs = valid_dates[valid_dates['Days Until Publication'] >= -30].copy()
                if not future_pubs.empty:
            # Create bins for the histogram
                    if not future_pubs.empty:
                        max_days = future_pubs['Days Until Publication'].max()
                        # Ensure step size is compatible with min/max values
                        bin_step = 30
                        max_bin = ((max_days // bin_step) + 1) * bin_step
                        bins = list(range(-30, int(max_bin) + bin_step, bin_step))
                        
                        fig = px.histogram(
                            future_pubs,
                            x='Days Until Publication',
                            title='Days Until Publication (Upcoming Books)',
                            labels={'Days Until Publication': 'Days Until Publication', 'count': 'Number of Books'},
                            nbins=len(bins)-1  # Use nbins instead of explicit bins
                        )
                    
                    # Add a vertical line at day 0 (today)
                    fig.add_vline(x=0, line_dash="dash", line_color="red")
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Display the full data table with filtering
            st.subheader("Publication Date Details")
            
            # Add status filter
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All", "Future", "Past", "Missing", "Malformed"],
                index=0
            )
            
            # Apply filter
            if status_filter != "All":
                filtered_df = pub_df[pub_df['Status'] == status_filter]
            else:
                filtered_df = pub_df
            
            # Display the filtered data
            if not filtered_df.empty:
                # Select columns to display
                display_cols = ['ISBN', 'Title', 'Publication Date', 'Days Until Publication', 'Status', 'Has Override']
                display_df = filtered_df[display_cols].copy()
                
                st.dataframe(display_df, use_container_width=True)
                
                # Export options
                if st.download_button(
                    label="Export to CSV",
                    data=display_df.to_csv(index=False),
                    file_name=f"publication_dates_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                ):
                    st.success("Data exported successfully!")
            else:
                st.info("No data matching the selected filter.")
        else:
            st.info("No preorder products found.")
    
    # Status Changes Tab
    with tabs[2]:
        st.subheader("Status Changes Report")
        
        # Date range selector
        col1, col2 = st.columns(2)
        
        with col1:
            # Default to last 30 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            report_start_date = st.date_input(
                "Start Date",
                value=start_date,
                max_value=end_date,
                key="status_start_date"
            )
        
        with col2:
            report_end_date = st.date_input(
                "End Date",
                value=end_date,
                max_value=end_date,
                key="status_end_date"
            )
        
        # Status change type selector
        status_type = st.selectbox(
            "Status Change Type",
            options=["All", "Released Preorders", "New Preorders", "Override Changes"],
            index=0
        )
        
        # Generate report button
        if st.button("Generate Status Change Report"):
            with st.spinner("Generating status change report..."):
                # This would typically connect to your data sources to get real data
                # For now, we'll simulate the report with test data
                if test_mode:
                    # Generate test status change data
                    status_changes = generate_test_status_changes(
                        report_start_date, 
                        report_end_date, 
                        status_type
                    )
                    
                    if status_changes:
                        # Display report summary
                        st.success("Status change report generated successfully!")
                        
                        # Calculate summary statistics
                        total_changes = len(status_changes)
                        
                        # Display summary
                        st.metric("Total Status Changes", total_changes)
                        
                        # Convert to DataFrame
                        changes_df = pd.DataFrame(status_changes)
                        
                        # Create a timeline chart if we have date data
                        if 'Change Date' in changes_df.columns:
                            # Convert to datetime
                            changes_df['Change Date'] = pd.to_datetime(changes_df['Change Date'])
                            
                            # Group by date and type
                            daily_changes = changes_df.groupby(['Change Date', 'Change Type']).size().reset_index(name='Count')
                            
                            # Create a line chart by change type
                            fig = px.line(
                                daily_changes,
                                x='Change Date',
                                y='Count',
                                color='Change Type',
                                title='Status Changes Over Time',
                                labels={'Count': 'Number of Changes', 'Change Date': 'Date'}
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Display the changes data
                        st.dataframe(changes_df, use_container_width=True)
                        
                        # Export option
                        if st.download_button(
                            label="Export to CSV",
                            data=changes_df.to_csv(index=False),
                            file_name=f"status_changes_{report_start_date}_to_{report_end_date}.csv",
                            mime="text/csv"
                        ):
                            st.success("Data exported successfully!")
                    else:
                        st.info("No status changes found for the selected period and type.")
                else:
                    st.warning("This feature requires API access. Enable test mode to see sample data.")
    
    # Custom Report Builder Tab
    with tabs[3]:
        st.subheader("Custom Report Builder")
        
        # Instructions
        st.markdown("""
        Build a custom report by selecting the data sources, filters, and display options below.
        """)
        
        # Data source selection
        st.subheader("1. Select Data Sources")
        
        data_sources = st.multiselect(
            "Data Sources",
            options=[
                "Preorder Products", 
                "Publication Dates", 
                "Preorder Tracking", 
                "Sales Data",
                "Approval History"
            ],
            default=["Preorder Products", "Publication Dates"]
        )
        
        if not data_sources:
            st.warning("Please select at least one data source.")
        else:
            # Date range filter (common to all reports)
            st.subheader("2. Set Time Period")
            
            col1, col2 = st.columns(2)
            
            with col1:
                custom_start_date = st.date_input(
                    "Start Date",
                    value=datetime.now().date() - timedelta(days=30),
                    key="custom_start_date"
                )
            
            with col2:
                custom_end_date = st.date_input(
                    "End Date",
                    value=datetime.now().date(),
                    key="custom_end_date"
                )
            
            # Additional filters based on selected data sources
            st.subheader("3. Set Filters")
            
            filters = {}
            
            if "Preorder Products" in data_sources:
                filters["collection"] = st.multiselect(
                    "Collections",
                    options=["Preorder", "Fiction", "Non-fiction", "Science Fiction", "Mystery", "Poetry"],
                    default=["Preorder"]
                )
            
            if "Publication Dates" in data_sources:
                filters["pub_date_status"] = st.multiselect(
                    "Publication Date Status",
                    options=["Future", "Past", "Missing", "Malformed"],
                    default=["Future", "Past"]
                )
            
            if "Sales Data" in data_sources:
                filters["min_quantity"] = st.number_input(
                    "Minimum Quantity",
                    min_value=0,
                    value=1,
                    key="min_quantity_filter"
                )
            
            # Display options
            st.subheader("4. Set Display Options")
            
            display_options = {}
            
            display_options["group_by"] = st.selectbox(
                "Group By",
                options=["None", "Publication Month", "Collection", "Status"]
            )
            
            display_options["sort_by"] = st.selectbox(
                "Sort By",
                options=["Title", "Publication Date", "Quantity", "ISBN"]
            )
            
            display_options["sort_order"] = st.radio(
                "Sort Order",
                options=["Ascending", "Descending"],
                horizontal=True
            )
            
            # Chart type if grouping is selected
            if display_options["group_by"] != "None":
                display_options["chart_type"] = st.selectbox(
                    "Chart Type",
                    options=["Bar Chart", "Line Chart", "Pie Chart"]
                )
            
            # Generate report button
            if st.button("Generate Custom Report"):
                with st.spinner("Generating custom report..."):
                    # This would typically connect to your data sources to get real data
                    # For now, we'll simulate the report with test data
                    if test_mode:
                        # Generate test data for custom report
                        custom_report_data = generate_test_custom_report(
                            data_sources,
                            custom_start_date,
                            custom_end_date,
                            filters,
                            display_options
                        )
                        
                        if custom_report_data:
                            # Display report summary
                            st.success("Custom report generated successfully!")
                            
                            # Convert to DataFrame
                            custom_df = pd.DataFrame(custom_report_data)
                            
                            # Display chart if grouping is selected
                            if display_options["group_by"] != "None" and display_options["group_by"] in custom_df.columns:
                                group_col = display_options["group_by"]
                                
                                # Group the data
                                if "Quantity" in custom_df.columns:
                                    grouped_data = custom_df.groupby(group_col)["Quantity"].sum().reset_index()
                                else:
                                    grouped_data = custom_df.groupby(group_col).size().reset_index(name="Count")
                                
                                # Create the appropriate chart
                                if display_options["chart_type"] == "Bar Chart":
                                    fig = px.bar(
                                        grouped_data,
                                        x=group_col,
                                        y="Quantity" if "Quantity" in grouped_data.columns else "Count",
                                        title=f"Data Grouped by {group_col}"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif display_options["chart_type"] == "Line Chart":
                                    fig = px.line(
                                        grouped_data,
                                        x=group_col,
                                        y="Quantity" if "Quantity" in grouped_data.columns else "Count",
                                        title=f"Data Grouped by {group_col}"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif display_options["chart_type"] == "Pie Chart":
                                    fig = px.pie(
                                        grouped_data,
                                        names=group_col,
                                        values="Quantity" if "Quantity" in grouped_data.columns else "Count",
                                        title=f"Data Grouped by {group_col}"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            # Display the data table
                            st.dataframe(custom_df, use_container_width=True)
                            
                            # Export option
                            if st.download_button(
                                label="Export to CSV",
                                data=custom_df.to_csv(index=False),
                                file_name=f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            ):
                                st.success("Data exported successfully!")
                        else:
                            st.info("No data found matching your criteria.")
                    else:
                        st.warning("This feature requires API access. Enable test mode to see sample data.")

# Helper function to generate test weekly report data
def generate_test_weekly_report(start_date, end_date):
    """Generate simulated weekly sales report data"""
    import random
    
    # Sample book titles and ISBNs
    books = [
        {"ISBN": "9781234567890", "Title": "Future Release Book"},
        {"ISBN": "9780262551311", "Title": "Modern Chinese Foodways"},
        {"ISBN": "9784756256522", "Title": "Fishes of Edo: A Guide to Classical Japanese Fishes"},
        {"ISBN": "9781234567891", "Title": "The Art of Baking"},
        {"ISBN": "9781234567892", "Title": "Machine Learning with Python"},
        {"ISBN": "9781234567893", "Title": "History of Ancient Rome"},
        {"ISBN": "9781234567894", "Title": "Modern Architecture"},
        {"ISBN": "9781234567895", "Title": "Advanced Mathematics"}
    ]
    
    # Generate random sales for each book
    report_data = []
    
    for book in books:
        # Random quantity (weighted towards lower numbers)
        quantity_weights = [0.6, 0.25, 0.1, 0.05]  # 60% chance of 1-5, 25% chance of 6-10, etc.
        quantity_ranges = [(1, 5), (6, 10), (11, 20), (21, 50)]
        
        # Select a quantity range based on weights
        selected_range = random.choices(quantity_ranges, weights=quantity_weights)[0]
        quantity = random.randint(selected_range[0], selected_range[1])
        
        # Skip some books randomly (50% chance)
        if random.random() > 0.5:
            report_data.append({
                "ISBN": book["ISBN"],
                "Title": book["Title"],
                "Quantity": quantity
            })
    
    return report_data

# Helper function to generate test status changes
def generate_test_status_changes(start_date, end_date, status_type):
    """Generate simulated status change data"""
    import random
    from datetime import datetime, timedelta
    
    status_changes = []
    
    # Generate random dates in the range
    current_date = start_date
    while current_date <= end_date:
        # Skip some days randomly
        if random.random() > 0.7:  # 30% chance of data on a given day
            current_date += timedelta(days=1)
            continue
        
        # Random number of changes for this day
        num_changes = random.randint(1, 3)
        
        for _ in range(num_changes):
            # Random ISBN
            isbn = f"978{random.randint(1000000000, 9999999999)}"
            
            # Random book title
            titles = [
                "Future Release Book",
                "Modern Chinese Foodways",
                "Fishes of Edo: A Guide to Classical Japanese Fishes",
                "The Art of Baking",
                "Machine Learning with Python",
                "History of Ancient Rome",
                "Modern Architecture",
                "Advanced Mathematics"
            ]
            title = random.choice(titles)
            
            # Change type based on filter or random if "All"
            if status_type != "All":
                change_type = status_type
            else:
                change_type = random.choice([
                    "Released Preorders", 
                    "New Preorders", 
                    "Override Changes"
                ])
            
            # Random details based on change type
            if change_type == "Released Preorders":
                old_status = "Preorder"
                new_status = "Released"
                quantity = random.randint(1, 10)
                details = f"Released {quantity} preordered copies"
            
            elif change_type == "New Preorders":
                old_status = "N/A"
                new_status = "Preorder"
                quantity = random.randint(1, 5)
                details = f"Added {quantity} new preorder(s)"
            
            else:  # Override Changes
                old_status = "Preorder"
                new_status = "Preorder"
                old_date = (current_date - timedelta(days=random.randint(10, 30))).strftime("%Y-%m-%d")
                new_date = (current_date + timedelta(days=random.randint(10, 30))).strftime("%Y-%m-%d")
                details = f"Changed publication date from {old_date} to {new_date}"
                quantity = 0
            
            # Add to status changes
            status_changes.append({
                "ISBN": isbn,
                "Title": title,
                "Change Date": current_date.strftime("%Y-%m-%d"),
                "Change Type": change_type,
                "Old Status": old_status,
                "New Status": new_status,
                "Quantity": quantity,
                "Details": details
            })
        
        # Move to next day
        current_date += timedelta(days=1)
    
    return status_changes

# Helper function to generate test custom report data
def generate_test_custom_report(data_sources, start_date, end_date, filters, display_options):
    """Generate simulated custom report data based on selected sources and filters"""
    import random
    from datetime import datetime, timedelta
    
    # Base set of books
    books = [
        {
            "ISBN": "9781234567890", 
            "Title": "Future Release Book",
            "Publication Date": (datetime.now().date() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "Publication Month": (datetime.now().date() + timedelta(days=30)).strftime("%Y-%m"),
            "Status": "Future",
            "Collection": "Preorder, Fiction"
        },
        {
            "ISBN": "9780262551311", 
            "Title": "Modern Chinese Foodways",
            "Publication Date": (datetime.now().date() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "Publication Month": (datetime.now().date() - timedelta(days=3)).strftime("%Y-%m"),
            "Status": "Past",
            "Collection": "Preorder, Non-fiction"
        },
        {
            "ISBN": "9784756256522", 
            "Title": "Fishes of Edo: A Guide to Classical Japanese Fishes",
            "Publication Date": (datetime.now().date() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "Publication Month": (datetime.now().date() - timedelta(days=5)).strftime("%Y-%m"),
            "Status": "Past",
            "Collection": "Preorder, Non-fiction"
        },
        {
            "ISBN": "9781234567891", 
            "Title": "The Art of Baking",
            "Publication Date": (datetime.now().date() + timedelta(days=15)).strftime("%Y-%m-%d"),
            "Publication Month": (datetime.now().date() + timedelta(days=15)).strftime("%Y-%m"),
            "Status": "Future",
            "Collection": "Preorder, Non-fiction"
        },
        {
            "ISBN": "9781234567892", 
            "Title": "Machine Learning with Python",
            "Publication Date": (datetime.now().date() + timedelta(days=45)).strftime("%Y-%m-%d"),
            "Publication Month": (datetime.now().date() + timedelta(days=45)).strftime("%Y-%m"),
            "Status": "Future",
            "Collection": "Preorder, Non-fiction"
        },
        {
            "ISBN": "9781234567893", 
            "Title": "History of Ancient Rome",
            "Publication Date": "",
            "Publication Month": "",
            "Status": "Missing",
            "Collection": "Preorder, Non-fiction"
        },
        {
            "ISBN": "9781234567894", 
            "Title": "Modern Architecture",
            "Publication Date": "Coming Soon",
            "Publication Month": "",
            "Status": "Malformed",
            "Collection": "Preorder, Non-fiction"
        },
        {
            "ISBN": "9781234567895", 
            "Title": "Advanced Mathematics",
            "Publication Date": (datetime.now().date() + timedelta(days=20)).strftime("%Y-%m-%d"),
            "Publication Month": (datetime.now().date() + timedelta(days=20)).strftime("%Y-%m"),
            "Status": "Future",
            "Collection": "Preorder, Non-fiction"
        }
    ]
    
    # Add sales data if requested
    if "Sales Data" in data_sources:
        for book in books:
            book["Quantity"] = random.randint(0, 20)
    
    # Add preorder tracking data if requested
    if "Preorder Tracking" in data_sources:
        for book in books:
            book["Preorder Quantity"] = random.randint(0, 10)
    
    # Add approval history if requested
    if "Approval History" in data_sources:
        for book in books:
            book["Approval Status"] = random.choice(["Approved", "Pending", "Not Submitted"])
            book["Approval Date"] = (datetime.now().date() - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d") if book["Approval Status"] == "Approved" else ""
    
    # Apply filters
    filtered_data = []
    
    for book in books:
        # Skip if doesn't match collection filter
        if "collection" in filters and filters["collection"]:
            matches_collection = False
            for collection in filters["collection"]:
                if collection in book["Collection"]:
                    matches_collection = True
                    break
            if not matches_collection:
                continue
        
        # Skip if doesn't match publication date status filter
        if "pub_date_status" in filters and filters["pub_date_status"]:
            if book["Status"] not in filters["pub_date_status"]:
                continue
        
        # Skip if doesn't match minimum quantity filter
        if "min_quantity" in filters and "Quantity" in book:
            if book["Quantity"] < filters["min_quantity"]:
                continue
        
        # Made it through all filters, add to results
        filtered_data.append(book)
    
    # Sort the data
    if display_options["sort_by"] in ["Title", "Publication Date", "Quantity", "ISBN"]:
        reverse = display_options["sort_order"] == "Descending"
        filtered_data.sort(key=lambda x: x.get(display_options["sort_by"], ""), reverse=reverse)
    
    return filtered_data