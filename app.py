import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context
import uuid
import os
import base64
from google.cloud import storage
from flask import Flask, send_from_directory, session

# --- Flask Server and Session Setup ---
server = Flask(__name__)
server.config['SECRET_KEY'] = os.urandom(24)

# --- Google Cloud Storage Setup ---
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'your-gcs-bucket-name')
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# --- Dash App Initialization ---
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# --- App Layout ---
app.layout = html.Div([
    dcc.Store(id='tasks-store', storage_type='session'),
    dbc.Container([
        html.H1("To-Do List"),
        dbc.Input(id='new-task-input', placeholder='Enter a new task...', type='text'),
        dcc.Upload(
            id='upload-attachment',
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
            },
            multiple=False
        ),
        dbc.Button('Add Task', id='add-task-button', n_clicks=0, className="mt-2"),
        html.Hr(),
        html.Div(id='task-list'),
        dbc.Modal([
            dbc.ModalHeader("Edit Task"),
            dbc.ModalBody([
                dbc.Input(id='edit-task-input', type='text'),
                dcc.Store(id='edit-task-id-store')
            ]),
            dbc.ModalFooter(
                dbc.Button("Save Changes", id="save-edit-button", className="ml-auto")
            ),
        ], id="edit-modal", is_open=False),
    ])
])

def create_task_list(tasks):
    if not tasks:
        return [html.P("No tasks yet!")]
    return [
        dbc.ListGroupItem([
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id={'type': 'task-checkbox', 'index': task['id']}, checked=task['completed']),
                    html.Span(task['label'], style={'textDecoration': 'line-through' if task['completed'] else 'none'})
                ], width=6),
                dbc.Col(html.A(task['attachment'], href=f"/download/{task['attachment']}") if task.get('attachment') else "", width=2),
                dbc.Col([
                    dbc.Button("Edit", id={'type': 'edit-button', 'index': task['id']}, size="sm", className="me-1"),
                    dbc.Button("Delete", id={'type': 'delete-button', 'index': task['id']}, size="sm", color="danger"),
                ], width=4, className="d-flex justify-content-end")
            ])
        ]) for task in tasks
    ]

@app.callback(
    Output('task-list', 'children'),
    Output('tasks-store', 'data'),
    Input('add-task-button', 'n_clicks'),
    Input('save-edit-button', 'n_clicks'),
    Input({'type': 'delete-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input({'type': 'task-checkbox', 'index': dash.dependencies.ALL}, 'checked'),
    State('new-task-input', 'value'),
    State('upload-attachment', 'contents'),
    State('upload-attachment', 'filename'),
    State('edit-task-input', 'value'),
    State('edit-task-id-store', 'data'),
    State('tasks-store', 'data'),
    prevent_initial_call=True
)
def update_tasks(add_clicks, save_clicks, delete_clicks, checkbox_values, new_task, attachment_contents, attachment_filename, edited_task, task_id_to_edit, tasks_data):
    tasks = tasks_data or []
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if 'add-task-button' in triggered_id and new_task:
        filename = None
        if attachment_contents:
            content_type, content_string = attachment_contents.split(',')
            decoded = base64.b64decode(content_string)
            filename = str(uuid.uuid4()) + '-' + attachment_filename
            blob = bucket.blob(filename)
            blob.upload_from_string(decoded)

        new_task_obj = {
            'id': str(uuid.uuid4()),
            'label': new_task,
            'completed': False,
            'attachment': filename
        }
        tasks.append(new_task_obj)

    elif 'save-edit-button' in triggered_id and edited_task and task_id_to_edit:
        for task in tasks:
            if task['id'] == task_id_to_edit:
                task['label'] = edited_task
                break

    elif 'delete-button' in triggered_id:
        task_id = eval(triggered_id)['index']
        task_to_delete = next((task for task in tasks if task['id'] == task_id), None)
        if task_to_delete:
            if task_to_delete.get('attachment'):
                blob = bucket.blob(task_to_delete['attachment'])
                if blob.exists():
                    blob.delete()
            tasks = [task for task in tasks if task['id'] != task_id]

    elif 'task-checkbox' in triggered_id:
        task_id = eval(triggered_id)['index']
        for task in tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                break

    return create_task_list(tasks), tasks

@app.callback(
    Output('edit-modal', 'is_open'),
    Output('edit-task-input', 'value'),
    Output('edit-task-id-store', 'data'),
    Input({'type': 'edit-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('save-edit-button', 'n_clicks'),
    State('tasks-store', 'data'),
    prevent_initial_call=True
)
def toggle_edit_modal(edit_clicks, save_clicks, tasks_data):
    tasks = tasks_data or []
    ctx = callback_context
    if not ctx.triggered or not any(c for c in edit_clicks if c is not None):
        return False, "", None

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'edit-button' in button_id:
        task_id = eval(button_id)['index']
        task = next((task for task in tasks if task['id'] == task_id), None)
        if task:
            return True, task['label'], task['id']

    return False, "", None

@server.route('/download/<path:filename>')
def download_file(filename):
    blob = bucket.blob(filename)
    if not blob.exists():
        return "File not found", 404
    
    temp_dir = "temp_downloads"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    destination_file_path = os.path.join(temp_dir, filename)
    blob.download_to_filename(destination_file_path)
    return send_from_directory(temp_dir, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8050)
