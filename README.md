# Preorder Admin Dashboard

This Streamlit-based dashboard provides comprehensive management and reporting tools for preorder books, publication dates, and sales data.

## Features

- **Dashboard Overview**: View key metrics and summaries of preorder status
- **Preorder Management**: Manage and monitor all preorder titles
- **Publication Date Overrides**: Edit and manage publication date information
- **Approval Workflow**: Review and process approvals for preorder releases
- **Sales Reports**: Generate and export various sales reports

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/preorder-dashboard.git
cd preorder-dashboard
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables by creating a `.env.production` file:
```
SHOP_URL=your-shop.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_access_token
GITHUB_TOKEN=your_github_token
GITHUB_REPOSITORY=owner/repo
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_SENDER=your@email.com
EMAIL_RECIPIENTS=recipient1@email.com,recipient2@email.com
```

## Usage

Run the dashboard using Streamlit:

```bash
streamlit run app.py
```

The dashboard will be available at http://localhost:8501 in your web browser.

## Project Structure

```
preorder_dashboard/
├── app.py                 # Main Streamlit application entry point
├── requirements.txt       # Dependencies
├── README.md              # Documentation
├── config/                # Configuration settings
├── data/                  # Data connectors and services
├── components/            # UI components
├── pages/                 # Dashboard pages
└── utils/                 # Utility functions
```

## Testing

You can run the dashboard in test mode without API connections by enabling the "Test Mode" toggle in the sidebar. This will use simulated data for all features.

## Development

To add a new feature or page to the dashboard:

1. Create a new page module in the `pages/` directory
2. Add the page to the sidebar navigation in `components/sidebar.py`
3. Register the page in the main app routing in `app.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
