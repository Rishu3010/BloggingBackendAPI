from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
DB_USERNAME = os.environ['DB_USERNAME']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = os.environ['DB_NAME']

app = Flask(__name__)

# Configure your database connection string
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # silence the deprecation warning
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY # JWT token secret key for signing the token

db = SQLAlchemy(app) # initialize SQLAlchemy
jwt = JWTManager(app) # initialize JWT manager


# Create the database models for SQLAlchemy

## User model for authentication and authorization
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

## Post model for the blog posts
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Create the database tables

@app.route('/')
def index():
    response=make_response("This is a simple blog api for crud operations along with authentication and authorization. <br/>Please your the following end points in any api-testing tool like Postman:-<br/>1. To register a user: <i>HOST</i>/register<br/>2. To login a user in order to get the access token: <i>HOST</i>/login<br/>3. To view, create, update, delete a post, use the endpoint with appropriate GET, POST, PUT, DELETE method, Endpoint : <i>HOST</i>/posts<br/>Note: /posts will fetch all the posts, while /posts/<i>int</i> will fetch taht particular post whose id is passed<br/>Note:- After logging in, make sure to add the access token to authorization header like this:-<br/>Authorization: Bearer <i>your_access_token</i>")
    response.headers['Content-Type'] = 'text/html'
    return response

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    hashed_password = generate_password_hash(password, method='sha256')

    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return make_response('Could not verify', 401)

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@app.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    title = request.json.get('title')
    content = request.json.get('content')
    current_user = get_jwt_identity()
    author = User.query.filter_by(username=current_user).first()
    post = Post(title=title, content=content, author_id=author.id)
    db.session.add(post)
    db.session.commit()

    return jsonify({"message": "Post created successfully!"}), 201


@app.route('/posts', methods=['GET'])
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id=None):
   
    if post_id is None:
        posts = Post.query.all()
        return jsonify([{"id": post.id, "title": post.title, "content": post.content} for post in posts]), 200
    
    else:
        post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found!"}), 404

    return jsonify(id=post.id, title=post.title, content=post.content), 200


@app.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found!"}), 404

    current_user = get_jwt_identity()
    if post.author.username != current_user:
        return jsonify({"message": "You are not authorized to update this post!"}), 403

    title = request.json.get('title')
    content = request.json.get('content')

    post.title = title
    post.content = content
    db.session.commit()

    return jsonify({"message": "Post updated successfully!"}), 200


@app.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found!"}), 404

    current_user = get_jwt_identity()
    if post.author.username != current_user:
        return jsonify({"message": "You are not authorized to delete this post!"}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({"message": "Post deleted successfully!"}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
