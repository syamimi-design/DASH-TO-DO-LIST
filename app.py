import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context
import uuid

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    dcc.Store(id='tasks-store', storage_type='session', data=[]),
    html.H1("To-Do List"),
    dbc.Input(id='new-task-input', placeholder='Enter a new task...', type='text'),
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

def create_task_list(tasks):
    if not tasks:
        return [html.P("No tasks yet!")]
    return [
        dbc.ListGroupItem([
            dbc.Row([
                dbc.Col(task['label'], width=8),
                dbc.Col([
                    dbc.Button("Edit", id={'type': 'edit-button', 'index': task['id']}, size="sm", className="me-1"),
                    dbc.Button("Delete", id={'type': 'delete-button', 'index': task['id']}, size="sm", color="danger"),
                ], width=4, className="d-flex justify-content-end")
            ])
        ]) for task in tasks
    ]

@app.callback(
    Output('tasks-store', 'data'),
    Output('new-task-input', 'value'),
    Input('add-task-button', 'n_clicks'),
    Input('save-edit-button', 'n_clicks'),
    State('new-task-input', 'value'),
    State('tasks-store', 'data'),
    State('edit-task-input', 'value'),
    State('edit-task-id-store', 'data'),
    prevent_initial_call=True
)
def update_tasks_storage(add_clicks, save_clicks, new_task, tasks, edited_task, task_id_to_edit):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'add-task-button' and new_task:
        new_task_obj = {'id': str(uuid.uuid4()), 'label': new_task}
        tasks.append(new_task_obj)
        return tasks, ''
    
    if triggered_id == 'save-edit-button' and edited_task and task_id_to_edit:
        for task in tasks:
            if task['id'] == task_id_to_edit:
                task['label'] = edited_task
                break
        return tasks, ''

    return tasks, ''

@app.callback(
    Output('task-list', 'children'),
    Input('tasks-store', 'data')
)
def display_tasks(tasks):
    return create_task_list(tasks)

@app.callback(
    Output('edit-modal', 'is_open'),
    Output('edit-task-input', 'value'),
    Output('edit-task-id-store', 'data'),
    Input({'type': 'edit-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('save-edit-button', 'n_clicks'),
    State('tasks-store', 'data'),
    prevent_initial_call=True
)
def toggle_edit_modal(edit_clicks, save_clicks, tasks):
    triggered = callback_context.triggered
    if not triggered:
        return False, "", None

    prop_id = triggered[0]['prop_id']
    
    if 'edit-button' in prop_id:
        if any(n_clicks > 0 for n_clicks in edit_clicks if n_clicks is not None):
            task_id = eval(prop_id.split('.')[0])['index']
            task_to_edit = next((task for task in tasks if task['id'] == task_id), None)
            if task_to_edit:
                return True, task_to_edit['label'], task_to_edit['id']

    return False, "", None

@app.callback(
    Output('tasks-store', 'data', allow_duplicate=True),
    Input({'type': 'delete-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    State('tasks-store', 'data'),
    prevent_initial_call=True
)
def delete_task(n_clicks, tasks):
    if not any(n_clicks):
        return tasks
    
    clicked_button_id = callback_context.triggered[0]['prop_id']
    task_id_to_delete = eval(clicked_button_id.split('.')[0])['index']
    
    updated_tasks = [task for task in tasks if task['id'] != task_id_to_delete]
    
    return updated_tasks

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8050)
