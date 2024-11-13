from flask import Flask, jsonify, request,  render_template, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS  # Importar CORS
from werkzeug.security import generate_password_hash, check_password_hash



# Configuración de la conexión
config = {
    'user': 'kioskocetec',        # Cambia esto por tu usuario
    'password': 'kioskocetec111',  # Cambia esto por tu contraseña
    'host': '10.9.120.5',         # Cambia esto si tu base de datos está en otro host
    'database': 'kioskocetec',      # Cambia esto por el nombre de tu base de datos
    'charset': 'utf8mb4'
}

app = Flask(__name__)
CORS(app)  # Habilitar CORS en toda la aplicación
CORS(app, resources={r"/login": {"origins": "http://localhost:3000"}})

app.config["JSON_AS_ASCII"] = False
@app.route("/productos")
def paginado():
    Paginado = None
    # Conexión a la base de datos
    db = mysql.connector.connect(**config)

    if 'Paginado' in request.args: #Si 'Paginado' esta en los argumentos de la respuesta
        pagina = int(request.args['Paginado']) #Convierte a int el numero de pagina

    if request.is_json:
        if 'Paginado' in request.json:
            pagina = request.json['Paginado']
        
    # Crear un cursor
    cursor = db.cursor(dictionary=True) 

    # Establecer el método para obtener resultados como diccionarios
    cursor.execute("SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'")

    # Consulta
    if Paginado == None: #Si pagina esta vacia
        query = "SELECT * FROM Productos"
        cursor.execute(query)
    else:
        elementos_por_pagina = 8
        paginas_descartadas = Paginado-1
        elementos_descartados = paginas_descartadas * elementos_por_pagina
        query = "SELECT * FROM Productos LIMIT (%s) OFFSET (%s)"
        cursor.execute(query, (elementos_por_pagina,
                               elementos_descartados,))
        #Por lo que entiendo se hace un calculo y se le pasa los valores a la consulta de SQL

    result = cursor.fetchall()


    # Cerrar cursor y conexión
    cursor.close()
    db.close()
    return jsonify(result)


@app.route("/categorias")
def categorias():
    db = mysql.connector.connect(**config)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'")
    query = "SELECT * FROM Categorias"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(result)

@app.route("signup", methods=("POST"),)
def agregarUsuario():
    db = mysql.connector.connect(**config)
    cursor = db.cursor(dictionary=True)
    nombre = request.json["nombre"]
    apellido = request.json["apellido"]
    curso = request.json["curso"]
    dirección = request.json["dirección"]
    Num_direccion = request.json["Num_direccion"]

    consulta = """INSERT INTO Usuario (Nombre , Apellido , Curso , Dirección , Num_direccion )
    VALUES (%s, %s, %s, %s, %s)"""
    cursor.execute(consulta, (nombre, apellido, curso, dirección, Num_direccion))

    db.commit()

@app.route("/marcas")
def marcas():
    db = mysql.connector.connect(**config)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'")
    query = "SELECT * FROM Marcas"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(result)

#PARA INSERTAR PRODUCTO FALTA DISE�AR
@app.route("/AñadirProducto", methods=('PUT',))
def insertar_producto():
    try:
        # Conexi�n a la base de datos
        db = mysql.connector.connect(**config)
        if db.is_connected():
            # Crear un cursor
            cursor = db.cursor()
            data = request.get_json()
            # Validar que todos los campos necesarios est�n presentes en el JSON
            required_fields = ['Nombre', 'Img',  'Precio_venta', 'Id_categoria', 'Id_marca']
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Faltan campos obligatorios"}), 400
            # Extraer los datos del producto
            precio_compra = 0
            nombre = data['Nombre']
            img = data['Img']
            precio_venta = data['Precio_venta']
            id_categoria = data['Id_categoria']
            id_marca = data['Id_marca']
            # Consulta SQL para insertar el producto
            # Consulta SQL corregida
            query_insertar = """
                INSERT INTO Productos (Id_marca, Id_categoria, Nombre, Img, Precio_venta, Precio_compra)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_insertar, (id_marca, id_categoria, nombre, img, precio_venta, precio_compra))

            db.commit()
            # Confirmar que el producto se insert� correctamente
            if cursor.rowcount == 1:
                # Obtener el ID del producto reci�n insertado
                id_producto = cursor.lastrowid
                cursor.close()
                return jsonify({"message": "Producto insertado correctamente", "Nombre": nombre}), 201
            else:
                cursor.close()
                return jsonify({"error": "Error al insertar el producto"}), 500

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if db.is_connected():
            db.close()


#PARA BUSCAR PRODUCTO
@app.route("/search", methods=["GET"])
def search():
    try:
        # Conexión a la base de datos
        db = mysql.connector.connect(**config)
        if db.is_connected():
            # Obtener el término de búsqueda desde los parámetros de la URL
            term = request.args.get('term', '')
            # Crear un cursor
            cursor = db.cursor(dictionary=True)
            cursor.execute("SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'")
            # Consulta SQL utilizando LIKE para buscar productos que coincidan parcialmente con el nombre
            query = "SELECT Id, Nombre, Precio_venta FROM Productos WHERE Nombre LIKE %s"
            cursor.execute(query, (f"%{term}%",))
            # Obtener los resultados
            results = cursor.fetchall()
            cursor.close()
            return jsonify(results), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if db.is_connected():
            db.close()


#FILTRAR PRODUCTOS POR CATEGORIA
@app.route("/categoria/<int:id>", methods=('GET',))
def productos_por_categoria(id):
   try:
       # Conexión a la base de datos
       db = mysql.connector.connect(**config)
       if db.is_connected():
           # Crear un cursor
           cursor = db.cursor(dictionary=True)
           cursor.execute("SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'")
           # 1. Consulta para obtener los productos de la categoría
           query_productos = "SELECT Cantidad_gramos, Id_categoria, Id, Id_marca, Img, Nombre, Precio_Compra, Precio_venta, Stock  FROM Productos WHERE Id_categoria = %s"
           cursor.execute(query_productos, (id,))
           productos = cursor.fetchall()
           # Si no hay productos en la categoría, devolver error 404
           if not productos:
               cursor.close()
               return jsonify({"error": "No se encontraron productos para esta categoría"}), 404
           cursor.close()
           return jsonify(productos)
   except mysql.connector.Error as e:
       return jsonify({"error": str(e)}), 500
   finally:
       if db.is_connected():
           db.close()



@app.route('/eliminar_producto', methods=['DELETE'])
def eliminar_producto():
    nombre_producto = request.json.get('Nombre')  # Recibe el nombre del producto desde el frontend

    if not nombre_producto:
        return jsonify({"error": "Nombre del producto es requerido"}), 400

    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        # Eliminar el producto basado en el nombre
        query = "DELETE FROM Productos WHERE Nombre = %s"
        cursor.execute(query, (nombre_producto,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Producto no encontrado"}), 404

        return jsonify({"message": "Producto eliminado exitosamente"}), 200

    except mysql.connector.Error as err:
        print(f"Error al eliminar producto: {err}")
        return jsonify({"error": "Error en la base de datos"}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

