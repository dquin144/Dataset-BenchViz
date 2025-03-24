import dash
from dash import html, dcc, Output, Input, State, no_update, dash_table
import dash_bootstrap_components as dbc
import requests

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Define the FastAPI backend URL
API_URL = "http://localhost:8000"

# Define the layout
app.layout = dbc.Container([
    dcc.Store(id='uploaded-data-store'),  # Add this for data persistence
    dbc.Row(
        dbc.Col(
            dbc.Tabs(
                [
                    dbc.Tab(label="Home", tab_id="home", children=[
                        dbc.Card(dbc.CardBody([
                            html.H4("Upload Dataset", className="mb-3"),
                            dcc.Upload(
                                id='upload-dataset',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select File')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px',
                                    'cursor': 'pointer',
                                    'transition': 'all 0.3s ease',
                                },
                                className='upload-box',
                                multiple=False,
                            ),
                            html.Div(id='upload-status'),
                            html.Hr(),
                            html.H5("Dataset Preview", id="dataset-title"),
                            # Just one loading spinner for the dataset display
                            dcc.Loading(
                                id="loading-dataset",
                                type="circle", 
                                color = "gray",
                                children=[html.Div(id='dataset-display')],
                            ),
                        ]), className="mt-3")
                    ]),
                    dbc.Tab(label="Benchmark", tab_id="benchmark", children=[
                        dbc.Card(dbc.CardBody("Benchmark content goes here."), className="mt-3")
                    ]),
                    dbc.Tab(label="Visualize", tab_id="visualize", children=[
                        dbc.Card(dbc.CardBody("Visualization content goes here."), className="mt-3")
                    ]),
                ],
                id="tabs",
                active_tab="home",
                className="mb-3 custom-tabs",
                style={"display": "flex", "justifyContent": "center", "borderBottom": "none"}, # Center the three tabs
            ),
            width=10  # Increased width for better table display
        ),
        justify="center",
    )
], fluid=True)

# Callback to handle file upload
@app.callback(
    [Output('upload-status', 'children'),
     Output('dataset-title', 'children'),
     Output('dataset-display', 'children')],
    Input('upload-dataset', 'contents'),
    State('upload-dataset', 'filename'),
    State('upload-dataset', 'last_modified')
)
def update_output(content, filename, date):
    if content is not None:
        # Content is available as a base64 string
        import base64
        import io
        
        # Decode the base64 string
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        
        # Create FormData-like structure for the request
        files = {'file': (filename, io.BytesIO(decoded), content_type)}
        
        try:
            # Send the file to the FastAPI backend
            response = requests.post(f"{API_URL}/upload/", files=files)
            
            if response.status_code == 200:
                # Get the dataset preview
                dataset_response = requests.get(f"{API_URL}/dataset/{filename}")
                
                if dataset_response.status_code == 200:
                    dataset_data = dataset_response.json()
                    
                    if 'error' in dataset_data:
                        return (
                            dbc.Alert(f"Successfully uploaded {filename}", color="success"),
                            f"Dataset Preview: {filename}",
                            dbc.Alert(f"Error loading data: {dataset_data['error']}", color="warning")
                        )
                    
                    # Create a data table
                    data_table = dash_table.DataTable(
                        id='dataset-table',
                        columns=[{"name": col, "id": col} for col in dataset_data['columns']],
                        data=dataset_data['data'],
                        page_size=10,
                        style_table={
                            'overflowX': 'auto',
                            'overflowY': 'scroll',  # vertical scrolling
                            'maxHeight': '395px',   # limit height
                            'margin': '20px 0',
                            'borderRadius': '5px',
                            'boxShadow': '0 2px 8px rgba(0,0,0,0.15)'
                        },
                        style_header={
                            'backgroundColor': '#f1f1f1',  # Light gray header
                            'color': '#333',  # Dark gray text
                            'fontWeight': 'bold',
                            'textAlign': 'left',
                            'border': 'none',  # Remove borders
                            'borderBottom': '1px solid #ddd'  # Only keep bottom border
                        },
                        style_cell={
                            'backgroundColor': 'white',
                            'color': '#333',
                            'textAlign': 'left',
                            'padding': '12px 15px',  # More padding
                            'minWidth': '100px', 
                            'width': '150px', 
                            'maxWidth': '200px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'border': 'none'  # Remove borders between cells
                        },
                        style_data={
                            'borderBottom': '1px solid #eee'  # Light border between rows
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#f9f9f9'  # Lighter gray for alternating rows
                            },
                            {
                                'if': {'state': 'selected'},
                                'backgroundColor': 'rgba(220, 220, 220, 0.5)',  # Light gray for selected cells
                                'border': '1px solid #ddd'
                            }
                        ],
                        style_as_list_view=True,  # Removes vertical grid lines
                        page_action='none',
                        sort_action='native',    # Add sorting capability
                        fixed_rows={'headers': True},
                        
                        # Add some interactivity
                        tooltip_data=[
                            {
                                column: {'value': str(value), 'type': 'text'}
                                for column, value in row.items()
                            } for row in dataset_data['data']
                        ],
                        tooltip_duration=None
                    )

                    # Add some container styling
                    table_container = html.Div(
                        [
                            data_table,
                            html.P(
                                f"Showing first {len(dataset_data['data'])} of {dataset_data['total_rows']} rows", 
                                style={
                                    'marginTop': '10px', 
                                    'fontSize': '0.9em', 
                                    'color': '#777',
                                    'textAlign': 'right'
                                }
                            )
                        ],
                        style={
                            'backgroundColor': 'white',
                            'padding': '20px',
                            'borderRadius': '8px',
                            'boxShadow': '0 2px 10px rgba(0,0,0,0.05)',
                            'marginTop': '20px'
                        }
                    )

                    # Return the styled container
                    return (
                        dbc.Alert(f"Successfully uploaded {filename}", color="success"),
                        f"Dataset Preview: {filename}",
                        table_container
                    )
                                        
                    total_rows_info = html.P(f"Showing first {len(dataset_data['data'])} of {dataset_data['total_rows']} rows", 
                                            style={'marginTop': '10px', 'fontSize': '0.9em', 'color': '#aaa'})
                    
                    return (
                        dbc.Alert(f"Successfully uploaded {filename}", color="success"),
                        f"Dataset Preview: {filename}",
                        html.Div([data_table, total_rows_info])
                    )
                else:
                    return (
                        dbc.Alert(f"Successfully uploaded {filename}", color="success"),
                        f"Dataset Preview: {filename}",
                        dbc.Alert(f"Error: Could not retrieve dataset preview", color="warning")
                    )
            else:
                return (
                    dbc.Alert(f"Error uploading file: {response.text}", color="danger"),
                    "Dataset Preview",
                    html.P("No dataset to display")
                )
        
        except Exception as e:
            return (
                dbc.Alert(f"Error: {str(e)}", color="danger"),
                "Dataset Preview",
                html.P("No dataset to display")
            )
    
    return no_update, no_update, html.P("Upload a dataset to see preview")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

