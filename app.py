import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context
import uuid
import os
import base64
import io
import zipfile
from flask import Flask, send_from_directory, session, redirect
from google.cloud import storage
from datetime import timedelta

# --- Flask Server and Session Setup ---
server = Flask(__name__)
server.config['SECRET_KEY'] = os.urandom(24)

# --- Google Cloud Storage Setup ---
BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'ojt252_bucket')
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# --- Dash App Initialization ---
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# --- App Layout ---
app.layout = html.Div([
    dcc.Store(id='tasks-store', storage_type='session'),
    dcc.Download(id="download-all-zip"),
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
        dbc.Row([
            dbc.Col(dbc.Button('Add Task', id='add-task-button', n_clicks=0, className="mt-2 w-100")),
            dbc.Col(dbc.Button('Download All Attachments', id='download-all-button', n_clicks=0, className="mt-2 w-100")),
        ]),
        html.Hr(),
        html.Div(id='task-list'),
        dbc.Modal([
            dbc.ModalHeader("Edit Task"),
            dbc.ModalBody([
                dbc.Input(id='edit-task-input', type='text'),
                html.Div(id='edit-attachment-display', className="mt-2"),
                dcc.Upload(
                    id='replace-attachment-upload',
                    children=html.Div(['Drag and Drop or ', html.A('Select File to Replace')]),
                    style={
                        'width': '100%', 'height': '60px', 'lineHeight': '60px',
                        'borderWidth': '1px', 'borderStyle': 'dashed',
                        'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'
                    },
                    multiple=False
                ),
                dbc.Button("Remove Attachment", id="remove-attachment-button", color="warning", className="mt-2", n_clicks=0),
                dcc.Store(id='edit-task-id-store')
            ]),
            dbc.ModalFooter(
                dbc.Button("Save Changes", id="save-edit-button", className="ml-auto")
            ),
        ], id="edit-modal", is_open=False),
    ])
])

def is_image_file(filename):
    if not filename:
        return False
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))

def create_task_list(tasks):
    if not tasks:
        return [html.P("No tasks yet!")]
    return [
        dbc.ListGroupItem([
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id={'type': 'task-checkbox', 'index': task['id']}, value=bool(task['completed'])),
                    html.Span(task['label'], style={'textDecoration': 'line-through' if task['completed'] else 'none'})
                ], width=6),
                dbc.Col(
                    html.A(
                        html.Img(src=f"/gcs/download/{task['attachment']}", style={'height':'50px'}),
                        href=f"/gcs/download/{task['attachment']}",
                        target="_blank" # Open in new tab
                    ) if is_image_file(task.get('attachment'))
                    else html.A(task['attachment'], href=f"/gcs/download/{task['attachment']}", target="_blank") if task.get('attachment') else "",
                    width=2
                ),
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
    Input({'type': 'task-checkbox', 'index': dash.dependencies.ALL}, 'value'),
    Input('remove-attachment-button', 'n_clicks'),
    State('new-task-input', 'value'),
    State('upload-attachment', 'contents'),
    State('upload-attachment', 'filename'),
    State('edit-task-input', 'value'),
    State('edit-task-id-store', 'data'),
    State('tasks-store', 'data'),
    State('replace-attachment-upload', 'contents'),
    State('replace-attachment-upload', 'filename'),
    prevent_initial_call=True
)
def update_tasks(add_clicks, save_clicks, delete_clicks, checkbox_values, remove_attachment_clicks, new_task, attachment_contents, attachment_filename, edited_task, task_id_to_edit, tasks_data, replace_contents, replace_filename):
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
            blob.upload_from_string(decoded, content_type=content_type)

        new_task_obj = {
            'id': str(uuid.uuid4()),
            'label': new_task,
            'completed': False,
            'attachment': filename
        }
        tasks.append(new_task_obj)

    elif 'save-edit-button' in triggered_id and task_id_to_edit:
        for task in tasks:
            if task['id'] == task_id_to_edit:
                if edited_task:
                    task['label'] = edited_task
                if replace_contents:
                    if task.get('attachment'):
                        old_blob = bucket.blob(task['attachment'])
                        if old_blob.exists():
                            old_blob.delete()
                    
                    content_type, content_string = replace_contents.split(',')
                    decoded = base64.b64decode(content_string)
                    new_filename = str(uuid.uuid4()) + '-' + replace_filename
                    new_blob = bucket.blob(new_filename)
                    new_blob.upload_from_string(decoded, content_type=content_type)
                    task['attachment'] = new_filename
                break
    
    elif 'remove-attachment-button' in triggered_id and task_id_to_edit:
        for task in tasks:
            if task['id'] == task_id_to_edit:
                if task.get('attachment'):
                    blob = bucket.blob(task['attachment'])
                    if blob.exists():
                        blob.delete()
                    task['attachment'] = None
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
        new_value = ctx.triggered[0]['value']
        for task in tasks:
            if task['id'] == task_id:
                task['completed'] = new_value
                break

    return create_task_list(tasks), tasks

@app.callback(
    Output('edit-modal', 'is_open'),
    Output('edit-task-input', 'value'),
    Output('edit-task-id-store', 'data'),
    Output('edit-attachment-display', 'children'),
    Input({'type': 'edit-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('save-edit-button', 'n_clicks'),
    State('tasks-store', 'data'),
    prevent_initial_call=True
)
def toggle_edit_modal(edit_clicks, save_clicks, tasks_data):
    tasks = tasks_data or []
    ctx = callback_context
    if not ctx.triggered or (not any(c for c in edit_clicks if c is not None) and not save_clicks):
        return False, "", None, None

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'edit-button' in button_id:
        task_id = eval(button_id)['index']
        task = next((task for task in tasks if task['id'] == task_id), None)
        if task:
            attachment_display = []
            if task.get('attachment'):
                if is_image_file(task['attachment']):
                    attachment_display = [html.Img(src=f"/gcs/download/{task['attachment']}", style={'height':'100px'})]
                else:
                    attachment_display = [html.A(task['attachment'], href=f"/gcs/download/{task['attachment']}", target="_blank")]
            return True, task['label'], task['id'], attachment_display

    return False, "", None, None

@server.route('/gcs/download/<path:filename>')
def download_gcs_file(filename):
    blob = bucket.blob(filename)
    if not blob.exists():
        return "File not found", 404
    
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="GET",
    )
    return redirect(signed_url)

@app.callback(
    Output("download-all-zip", "data"),
    Input("download-all-button", "n_clicks"),
    State("tasks-store", "data"),
    prevent_initial_call=True,
)
def download_all_attachments(n_clicks, tasks_data):
    tasks = tasks_data or []
    attachments = [task['attachment'] for task in tasks if task.get('attachment')]

    if not attachments:
        return None

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in attachments:
            blob = bucket.blob(filename)
            if blob.exists():
                file_bytes = blob.download_as_bytes()
                zf.writestr(filename, file_bytes)

    memory_file.seek(0)
    return dcc.send_bytes(memory_file.getvalue(), "attachments.zip")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8050)
