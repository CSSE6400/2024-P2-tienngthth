from flask import Blueprint, jsonify, request 
from todo.models import db 
from todo.models.todo import Todo 
from datetime import datetime
from marshmallow import ValidationError, Schema, fields
 
ToDoPostSchema = Schema.from_dict({
   "title": fields.Str(required=True), 
    "description": fields.Str(required=True),
    "completed": fields.Boolean(),
    "deadline_at": fields.Str(),
})

ToDoPutSchema = Schema.from_dict({
   "title": fields.Str(), 
    "description": fields.Str(),
    "completed": fields.Boolean(),
    "deadline_at": fields.Str(),
})

api = Blueprint('api', __name__, url_prefix='/api/v1') 

@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET']) 
def get_todos():
   todos = Todo.query.all() 
   complete_filter = request.args.get('completed', default=False, type=bool)
   window = request.args.get('window', type=int)
   if window:
    todos = [todo for todo in todos if (todo.deadline_at is not None) |  (abs(todo.deadline_at - datetime.now())).days <= window]
   result = [] 
   for todo in todos: 
      if (complete_filter == True):
            if (todo.completed == True):
                result.append(todo.to_dict()) 
      else :
        result.append(todo.to_dict()) 
   return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET']) 
def get_todo(todo_id): 
   todo = Todo.query.get(todo_id) 
   if todo is None: 
      return jsonify({'error': 'Todo not found'}), 404 
   return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST']) 
def create_todo(): 
    try:
      result = ToDoPostSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    todo = Todo( 
      title=request.json.get('title'), 
      description=request.json.get('description'), 
      completed=request.json.get('completed', False), 
    ) 
    if 'deadline_at' in request.json: 
      todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at')) 
 
    # Adds a new record to the database or will update an existing record 
    db.session.add(todo) 
    # Commits the changes to the database, this must be called for the changes to be saved 
    db.session.commit() 
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT']) 
def update_todo(todo_id): 
    try:
      result = ToDoPutSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    todo = Todo.query.get(todo_id) 
    if todo is None: 
        return jsonify({'error': 'Todo not found'}), 404 
 
    todo.title = request.json.get('title', todo.title) 
    todo.description = request.json.get('description', todo.description) 
    todo.completed = request.json.get('completed', todo.completed) 
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at) 
    db.session.commit() 
 
    return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE']) 
def delete_todo(todo_id): 
   todo = Todo.query.get(todo_id) 
   if todo is None: 
      return jsonify({}), 200 
 
   db.session.delete(todo) 
   db.session.commit() 
   return jsonify(todo.to_dict()), 200
