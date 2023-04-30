from flask import Flask, request, jsonify, session
import mysql.connector
from flask_bcrypt import Bcrypt
from functools import wraps

app = Flask(__name__)
app.secret_key = 'Viernesgarage3103+'
bcrypt = Bcrypt(app)


db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Viernesgarage3103+",
    database="cheques_blockchain"
)

def is_authenticated():
    return 'user_id' in session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return jsonify({"status": "error", "message": "Autenticación requerida."}), 401
        return f(*args, **kwargs)
    return decorated_function



@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    username = data['username']
    password = data['password']

    # Cifrar la contraseña antes de guardarla en la base de datos
    hashed_password = bcrypt.generate_password_hash(password.encode('utf-8'))

    cursor = db_connection.cursor()
    try:
        # Insertar el nuevo usuario en la base de datos
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (username, hashed_password))
        db_connection.commit()
        return jsonify({"status": "success", "message": "Usuario registrado exitosamente."})
    except Exception as e:
        db_connection.rollback()
        return jsonify({"status": "error", "message": "Error al registrar el usuario. Detalle: {}".format(str(e))})




@app.route('/clientes', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def clientes():
    cursor = db_connection.cursor()
    
    if request.method == 'GET':
        # Obtener datos del cliente de la base de datos y devolver como JSON
        cursor.execute("SELECT * FROM clientes")
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        result = [dict(zip(column_names, row)) for row in rows]
        return jsonify(result)

    elif request.method == 'POST':
        # Agregar un nuevo cliente a la base de datos
        data = request.get_json()
        cursor.execute("INSERT INTO clientes (DNI, NOMBRE, CBU, ADDRESS) VALUES (%s, %s, %s, %s)",
                       (data['DNI'], data['NOMBRE'], data['CBU'], data['ADDRESS']))
        db_connection.commit()
        return jsonify({"status": "success", "message": "Cliente creado con éxito."})

    elif request.method == 'PUT':
        # Actualizar los datos de un cliente existente
        data = request.get_json()
        cursor.execute("UPDATE clientes SET NOMBRE=%s, CBU=%s, ADDRESS=%s WHERE DNI=%s",
                       (data['NOMBRE'], data['CBU'], data['ADDRESS'], data['DNI']))
        db_connection.commit()
        return jsonify({"status": "success", "message": "Cliente actualizado con éxito."})

    elif request.method == 'DELETE':
        # Eliminar un cliente de la base de datos
        dni = request.args.get('dni')
        cursor.execute("DELETE FROM clientes WHERE DNI=%s", (dni,))
        db_connection.commit()
        return jsonify({"status": "success", "message": "Cliente eliminado con éxito."})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print("data:", data)
    username = data['username']
    password = data['password']

    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username=%s", (username,))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user[2], password.encode('utf-8')):
        # Iniciar sesión del usuario
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['role'] = user[3]
        return jsonify({"status": "success", "message": "Inicio de sesión exitoso."})
    else:
        return jsonify({"status": "error", "message": "Nombre de usuario o contraseña incorrectos."})


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    # session.pop('user_id', None)
    # session.pop('username', None)
    # session.pop('role', None)
    return jsonify({"status": "success", "message": "Sesión cerrada con éxito."})



if __name__ == "__main__":
    app.run(debug=True)



