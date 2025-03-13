"""
Preorder Management Page for the Preorder Admin Dashboard.

This module provides the interface for managing preorder products and tracking sales.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Initialize data service
from data.data_service import DataService

def show_preorder_management():
    """
    Display the preorder management page.
    """
    # Initialize data service with test mode from session state
    test_mode = st.session_state.get('test_mode', False)
    data_service = DataService(test_mode=test_mode)
    
    # Create tabs for different sections
    tabs = st.tabs(["Current Preorders", "Preorder Tracking", "Sales Analysis"])
    
    # Current Preorders Tab
    with tabs[0]:
        st.subheader("Current Preorder Products")
        
        with st.spinner("Loading preorder products..."):
            # Get preorder products
            preorder_products = data_service.get_preorder_products()
            
            # Get publication date overrides
            overrides = data_service.get_pub_date_overrides()
        
        # Filter and search options
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            search_term = st.text_input("Search by Title or ISBN", key="preorder_search")
        
        with col2:
            # Publication date filter
            date_filter = st.selectbox(
                "Filter by Publication Date",
                options=["All", "Future Dates", "Past Dates", "Next 30 Days", "Missing Dates", "Malformed Dates"],
                index=0
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sort By",
                options=["Title", "Publication Date"],
                index=1
            )
        
        # Process and filter products
        filtered_products = []
        today = datetime.now().date()
        
        for product in preorder_products:
            # Get barcode/ISBN
            barcode = product.get('barcode')
            
            # Skip products without barcode
            if not barcode:
                continue
            
            # Check for override
            if barcode in overrides:
                product['pub_date_original'] = product.get('pub_date')
                product['pub_date'] = overrides[barcode]
                product['has_override'] = True
            else:
                product['pub_date_original'] = None
                product['has_override'] = False
            
            # Apply search filter
            if search_term:
                if (search_term.lower() not in product.get('title', '').lower() and
                    search_term not in str(barcode)):
                    continue
            
            # Parse and validate publication date
            pub_date = None
            is_malformed = False
            pub_date_str = product.get('pub_date')
            
            if not pub_date_str:
                is_missing = True
            else:
                is_missing = False
                try:
                    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d').date()
                except ValueError:
                    is_malformed = True
            
            # Store date and validation flags
            product['pub_date_obj'] = pub_date
            product['is_missing_date'] = is_missing
            product['is_malformed_date'] = is_malformed
            
            # Apply date filter
            if date_filter == "Future Dates" and (is_missing or is_malformed or pub_date <= today):
                continue
            elif date_filter == "Past Dates" and (is_missing or is_malformed or pub_date > today):
                continue
            elif date_filter == "Next 30 Days" and (is_missing or is_malformed or pub_date > today + timedelta(days=30) or pub_date < today):
                continue
            elif date_filter == "Missing Dates" and not is_missing:
                continue
            elif date_filter == "Malformed Dates" and not is_malformed:
                continue
            
            # Add to filtered products
            filtered_products.append(product)
        
        # Sort products
        if sort_by == "Title":
            filtered_products.sort(key=lambda x: x.get('title', '').lower())
        else:  # Publication Date
            # Define a key function that handles various date scenarios
            def get_sort_key(product):
                if product.get('is_missing_date'):
                    return datetime.max  # Put missing dates at the end
                elif product.get('is_malformed_date'):
                    return datetime.max - timedelta(days=1)  # Put malformed dates before missing dates
                else:
                    return product.get('pub_date_obj', datetime.max)
            
            filtered_products.sort(key=get_sort_key)
        
        # Display filter summary
        st.write(f"Showing {len(filtered_products)} of {len(preorder_products)} preorder products")
        
        # Create a DataFrame for display
        display_data = []
        for product in filtered_products:
            # Format the publication date for display
            if product.get('is_missing_date'):
                display_pub_date = "Missing"
            elif product.get('is_malformed_date'):
                display_pub_date = f"Invalid: {product.get('pub_date')}"
            else:
                display_pub_date = product.get('pub_date')
            
            # Create a display row
            display_row = {
                'ISBN': product.get('barcode'),
                'Title': product.get('title'),
                'Publication Date': display_pub_date
            }
            
            # Add override information if available
            if product.get('has_override'):
                display_row['Original Date'] = product.get('pub_date_original', 'Unknown')
                display_row['Override Applied'] = '✓'
            
            # Add to display data
            display_data.append(display_row)
        
        # Create DataFrame for display
        if display_data:
            display_df = pd.DataFrame(display_data)
            
            # Apply styling based on date status
            def style_pub_date(val):
                if val == "Missing":
                    return 'background-color: #ffcdd2'  # Light red
                elif val.startswith("Invalid"):
                    return 'background-color: #ffcdd2'  # Light red
                else:
                    try:
                        date_val = datetime.strptime(val, '%Y-%m-%d').date()
                        if date_val < today:
                            return 'background-color: #fff9c4'  # Light yellow
                        else:
                            return ''
                    except:
                        return ''
            
            # Convert to Streamlit DataFrame
            st.dataframe(display_df, use_container_width=True)
            
            # Add buttons for managing selected products
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("View Details", key="view_details"):
                    st.info("Product detail view not yet implemented")
            
            with col2:
                if st.button("Edit Publication Date", key="edit_pub_date"):
                    st.session_state.current_page = "override_management"
                    st.experimental_rerun()
            
            with col3:
                if st.button("Mark for Approval", key="mark_for_approval"):
                    st.info("Approval marking not yet implemented")
        else:
            st.info("No products match your filters.")
    
    # Preorder Tracking Tab
    with tabs[1]:
        st.subheader("Preorder Tracking Data")
        
        with st.spinner("Loading preorder tracking data..."):
            # Get preorder tracking data
            tracking_data = data_service.get_preorder_tracking_data()
        
        if isinstance(tracking_data, pd.DataFrame) and not tracking_data.empty:
            # Summary statistics
            total_preorders = tracking_data['Quantity'].sum()
            unique_titles = tracking_data['Title'].nunique()
            
            # Display summary
            st.markdown(f"**Total tracked preorders:** {total_preorders:,} copies")
            st.markdown(f"**Unique titles:** {unique_titles}")
            
            # Group by publication date
            if 'Pub Date' in tracking_data.columns:
                # Remove rows with missing dates for this analysis
                date_data = tracking_data.dropna(subset=['Pub Date'])
                
                if not date_data.empty:
                    try:
                        # Convert to datetime for grouping
                        date_data['Pub Date'] = pd.to_datetime(date_data['Pub Date'])
                        
                        # Group by month
                        date_data['Month'] = date_data['Pub Date'].dt.strftime('%Y-%m')
                        monthly_summary = date_data.groupby('Month').agg({
                            'Quantity': 'sum',
                            'ISBN': 'nunique'
                        }).reset_index()
                        
                        # Rename columns
                        monthly_summary = monthly_summary.rename(columns={
                            'ISBN': 'Unique Titles'
                        })
                        
                        # Sort by month
                        monthly_summary = monthly_summary.sort_values('Month')
                        
                        # Create a bar chart
                        fig = px.bar(
                            monthly_summary,
                            x='Month',
                            y='Quantity',
                            title='Preorders by Publication Month',
                            labels={'Quantity': 'Preordered Copies', 'Month': 'Publication Month'},
                            text='Quantity'
                        )
                        
                        # Add title count as a line on secondary y-axis
                        fig.add_trace(
                            go.Scatter(
                                x=monthly_summary['Month'],
                                y=monthly_summary['Unique Titles'],
                                mode='lines+markers',
                                name='Unique Titles',
                                yaxis='y2'
                            )
                        )
                        
                        # Update layout for dual y-axis
                        fig.update_layout(
                            yaxis2=dict(
                                title='Unique Titles',
                                overlaying='y',
                                side='right'
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creating publication date chart: {e}")
            
            # Display the full tracking data with filters
            st.subheader("Detailed Tracking Data")
            
            # Add filters for the tracking data
            col1, col2 = st.columns(2)
            
            with col1:
                search_title = st.text_input("Search by Title", key="tracking_search")
            
            with col2:
                status_filter = st.selectbox(
                    "Filter by Status",
                    options=["All"] + tracking_data['Status'].unique().tolist(),
                    index=0
                )
            
            # Apply filters
            filtered_tracking = tracking_data.copy()
            
            if search_title:
                filtered_tracking = filtered_tracking[filtered_tracking['Title'].str.contains(search_title, case=False)]
            
            if status_filter != "All":
                filtered_tracking = filtered_tracking[filtered_tracking['Status'] == status_filter]
            
            # Show the filtered data
            st.dataframe(filtered_tracking, use_container_width=True)
            
            # Export option
            if st.download_button(
                label="Export to CSV",
                data=filtered_tracking.to_csv(index=False),
                file_name="preorder_tracking_export.csv",
                mime="text/csv"
            ):
                st.success("Data exported successfully!")
        else:
            st.info("No preorder tracking data available.")
    
    # Sales Analysis Tab
    with tabs[2]:
        st.subheader("Preorder Sales Analysis")
        
        # Date range selector for analysis
        col1, col2 = st.columns(2)
        
        with col1:
            days_back = st.slider(
                "Days to Analyze",
                min_value=7,
                max_value=90,
                value=30,
                step=7
            )
        
        with col2:
            # This would typically connect to the Shopify API to get sales data
            # For now, we'll simulate this with our test data
            if st.button("Refresh Sales Data", key="refresh_sales"):
                st.info("Refreshing sales data...")
                time.sleep(1)  # Simulate API call
        
        # Placeholder for sales data
        # In a real implementation, this would call data_service.get_preorder_sales(days=days_back)
        if test_mode:
            # Generate simulated sales data
            sales_data = generate_test_sales_data(days_back)
            
            if sales_data:
                # Convert to DataFrame
                sales_df = pd.DataFrame(sales_data)
                
                # Convert dates for analysis
                sales_df['created_at'] = pd.to_datetime(sales_df['created_at'])
                sales_df['date'] = sales_df['created_at'].dt.date
                
                # Group by date
                daily_sales = sales_df.groupby('date').agg({
                    'quantity': 'sum',
                    'order_id': 'nunique'
                }).reset_index()
                
                # Rename columns
                daily_sales = daily_sales.rename(columns={
                    'order_id': 'orders'
                })
                
                # Sort by date
                daily_sales = daily_sales.sort_values('date')
                
                # Create a line chart
                fig = px.line(
                    daily_sales,
                    x='date',
                    y='quantity',
                    title=f'Daily Preorder Sales (Last {days_back} Days)',
                    labels={'quantity': 'Copies Sold', 'date': 'Date'},
                    markers=True
                )
                
                # Add order count as a bar chart
                fig.add_trace(
                    go.Bar(
                        x=daily_sales['date'],
                        y=daily_sales['orders'],
                        name='Orders',
                        opacity=0.3,
                        yaxis='y2'
                    )
                )
                
                # Update layout for dual y-axis
                fig.update_layout(
                    yaxis2=dict(
                        title='Order Count',
                        overlaying='y',
                        side='right'
                    ),
                    barmode='overlay'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show top selling titles
                st.subheader("Top Selling Preorder Titles")
                
                # Group by title
                title_sales = sales_df.groupby(['title', 'barcode']).agg({
                    'quantity': 'sum'
                }).reset_index().sort_values('quantity', ascending=False)
                
                # Display top 10
                st.dataframe(title_sales.head(10), use_container_width=True)
                
                # Show full sales data with a toggle
                if st.checkbox("Show Full Sales Data"):
                    st.dataframe(sales_df, use_container_width=True)
            else:
                st.info("No sales data available for the selected period.")
        else:
            st.warning("This feature requires API access to Shopify. Enable test mode to see sample data.")

# Helper function to generate test sales data
def generate_test_sales_data(days_back):
    """Generate simulated sales data for testing"""
    import random
    from datetime import datetime, timedelta
    
    sales_data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Sample book titles
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
    
    # Generate random sales for each day
    current_date = start_date
    while current_date <= end_date:
        # Random number of orders for this day
        num_orders = random.randint(1, 5)
        
        for i in range(num_orders):
            # Random order details
            order_id = f"order_{current_date.strftime('%Y%m%d')}_{i}"
            order_name = f"#{random.randint(1000, 9999)}"
            
            # Random number of line items in this order
            num_items = random.randint(1, 3)
            
            for j in range(num_items):
                # Select a random title
                title_idx = random.randint(0, len(titles) - 1)
                title = titles[title_idx]
                
                # Generate a random ISBN
                isbn = f"978{random.randint(1000000000, 9999999999)}"
                
                # Random quantity (weighted towards 1)
                quantity_weights = [0.7, 0.2, 0.1]  # 70% chance of 1, 20% chance of 2, 10% chance of 3
                quantity = random.choices([1, 2, 3], weights=quantity_weights)[0]
                
                # Random time during the day
                random_hour = random.randint(8, 22)
                random_minute = random.randint(0, 59)
                order_time = current_date.replace(hour=random_hour, minute=random_minute)
                
                # Add to sales data
                sales_data.append({
                    'order_id': order_id,
                    'order_name': order_name,
                    'created_at': order_time.isoformat(),
                    'barcode': isbn,
                    'title': title,
                    'quantity': quantity
                })
        
        # Move to next day
        current_date += timedelta(days=1)
    
    return sales_data