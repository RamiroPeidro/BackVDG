from flask import Flask, request, jsonify, session
from flask_cors import CORS, cross_origin
import mysql.connector
from flask_bcrypt import Bcrypt
from functools import wraps
import os

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
app.config['SESSION_COOKIE_DOMAIN'] = 'http://localhost:3000'
app.secret_key = 'Viernesgarage3103+'
bcrypt = Bcrypt(app)

app.config.update(
    SESSION_COOKIE_SAMESITE="None", 
    SESSION_COOKIE_ENABLED=True
)
app.config['SESSION_COOKIE_DOMAIN'] = None

# user = os.environ['DB_USER']
# password = os.environ['DB_PASSWORD']
# host = os.environ['DB_HOST']
# database = os.environ['DB_NAME']

# db_connection = mysql.connector.connect(
#     host=host,
#     user=user,
#     password=password,
#     database=database
# )

db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Viernesgarage3103+",
    database="cheques_blockchain"
)

def is_authenticated():
    for u in session:
        print(u)
    return 'user_id' in session

def fetch_data(query):
    cursor = db_connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    result = [dict(zip(column_names, row)) for row in rows]
    return jsonify(result)

def handle_post_put(method):
    data = request.get_json()
    cursor = db_connection.cursor()
    if method == 'POST':
        cursor.execute("INSERT INTO clientes (user_id, dni, nombre, cbu, address, username) VALUES (%s, %s, %s, %s, %s, %s)",
                       (data['user_id'], data['dni'], data['nombre'], data['cbu'], data['address'], data['username']))
        db_connection.commit()
        return jsonify({"status": "success", "message": "Cliente creado con éxito."})
    elif method == 'PUT':
        cursor.execute("UPDATE clientes SET user_id=%s, nombre=%s, cbu=%s, address=%s, username=%s WHERE dni=%s",
                       (data['user_id'], data['nombre'], data['cbu'], data['address'], data['username'], data['dni']))
        db_connection.commit()
        return jsonify({"status": "success", "message": "Cliente actualizado con éxito."})

def handle_delete():
    dni = request.args.get('dni')
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM clientes WHERE dni=%s", (dni,))
    db_connection.commit()
    return jsonify({"status": "success", "message": "Cliente eliminado con éxito."})


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return jsonify({"status": "error", "message": "Autenticación requerida."}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/signup', methods=['POST'])
@cross_origin(supports_credentials=True)
def signup():
    data = request.get_json()

    try:
        dni, nombre, cbu, address, username, password, mnemonic = data.values()

        hashed_password = bcrypt.generate_password_hash(password.encode('utf-8'))

        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO usuarios (username, password, mnemonic) VALUES (%s, %s, %s)", (username, hashed_password, mnemonic))
        db_connection.commit()

        cursor.execute("SELECT LAST_INSERT_ID();")
        user_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO clientes (user_id, dni, nombre, cbu, address, usuario) VALUES (%s, %s, %s, %s, %s, %s)",
                       (user_id, dni, nombre, cbu, address, username))
        db_connection.commit()

        return jsonify({"status": "success", "message": "Usuario registrado exitosamente."})
    except Exception as e:
        db_connection.rollback()
        return jsonify({"status": "error", "message": "Error al registrar el usuario. Detalle: {}".format(str(e))})

@app.route('/usuarios', methods=['GET'])
@cross_origin(supports_credentials=True)
def usuarios():
    return fetch_data("SELECT * FROM usuarios")

@app.route('/clientes', methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin(supports_credentials=True)
@login_required
def clientes():
    if request.method == 'GET':
        return fetch_data("SELECT * FROM clientes")
    elif request.method in ['POST', 'PUT']:
        return handle_post_put(request.method)
    elif request.method == 'DELETE':
        return handle_delete()

@app.route('/login', methods=['POST'])
@cross_origin(supports_credentials=True)
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    cursor = db_connection.cursor()
    cursor.execute("SELECT id, username, password, role, mnemonic FROM usuarios WHERE username=%s", (username,))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user[2], password.encode('utf-8')):
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['role'] = user[3]
        session['mnemonic'] = user[4]
        return jsonify({"status": "success", "message": "Inicio de sesión exitoso."})
    else:
        return jsonify({"status": "error", "message": "Nombre de usuario o contraseña incorrectos."})

@app.route('/logout', methods=['POST'])
@cross_origin(supports_credentials=True)
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Sesión cerrada con éxito."})

if __name__ == "__main__":
    app.run(debug=True)

