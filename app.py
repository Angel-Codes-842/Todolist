from flask import Flask, request, render_template, redirect, session, flash
import sqlite3
import hashlib
import os

app = Flask(__name__)
# Genera una clave secreta aleatoria para la aplicación
app.secret_key = os.urandom(24)

# Función para establecer conexión con la base de datos
def get_db_connection():
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
    return conn

# Función para hashear contraseñas
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Ruta principal, muestra la página de inicio o redirige al login
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')

# Ruta para registrar nuevos usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = hash_password(request.form['contraseña'])
        
        conn = get_db_connection()
        try:
            # Verifica si es el primer usuario
            is_first_user = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0] == 0
            
            # Inserta el nuevo usuario en la base de datos
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (nombre, correo, contraseña, es_admin) VALUES (?, ?, ?, ?)', 
                           (nombre, correo, contraseña, is_first_user))
            
            new_user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Inicia sesión automáticamente
            session['user_id'] = new_user_id
            if is_first_user:
                flash('Cuenta de administrador creada con éxito', 'success')
            else:
                flash('Cuenta creada con éxito', 'success')
            return redirect('/')
        except sqlite3.IntegrityError:
            conn.close()
            flash('El correo ya está registrado', 'error')
    
    return render_template('register.html')

# Ruta para iniciar sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        
        if correo == 'admin@gmail.com' and contraseña == 'admin123':
            session['user_id'] = 'admin@gmail.com'
            flash('Bienvenido, Administrador', 'success')
            return redirect('/admin')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE correo = ?', (correo,)).fetchone()
        conn.close()
        
        if user and hashlib.sha256(contraseña.encode()).hexdigest() == user['contraseña']:
            session['user_id'] = user['id']
            flash('Inicio de sesión exitoso', 'success')
            return redirect('/')
        else:
            flash('Credenciales incorrectas', 'error')
    
    return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

# Ruta para añadir una nueva tarea
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/login')
    
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    fecha = request.form['fecha']
    
    conn = get_db_connection()
    # Inserta la nueva tarea en la base de datos
    conn.execute('INSERT INTO tareas (usuario_id, nombre, descripcion, fecha) VALUES (?, ?, ?, ?)', 
                 (session['user_id'], nombre, descripcion, fecha))
    conn.commit()
    conn.close()
    
    flash('Tarea añadida correctamente', 'success')
    return redirect('/view_tasks')

# Ruta para eliminar una tarea
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    # Elimina la tarea de la base de datos
    conn.execute('DELETE FROM tareas WHERE id = ? AND usuario_id = ?', (task_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Tarea eliminada correctamente', 'success')
    return redirect('/view_tasks')

# Ruta para marcar una tarea como completada
@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    # Actualiza el estado de la tarea a completada
    conn.execute('UPDATE tareas SET completada = TRUE WHERE id = ? AND usuario_id = ?', (task_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Tarea marcada como completada', 'success')
    return redirect('/view_tasks')

# Ruta para ver todas las tareas
@app.route('/view_tasks')
def view_tasks():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    # Obtiene las tareas pendientes y completadas del usuario
    tareas_pendientes = conn.execute('SELECT * FROM tareas WHERE usuario_id = ? AND completada = FALSE', 
                                     (session['user_id'],)).fetchall()
    tareas_completadas = conn.execute('SELECT * FROM tareas WHERE usuario_id = ? AND completada = TRUE', 
                                      (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('view_tasks.html', tareas_pendientes=tareas_pendientes, tareas_completadas=tareas_completadas)

#-------------------------------------------------
#Funciones para el admin

# Función para verificar si el usuario es administrador
def is_admin():
    return session.get('user_id') == 'admin@gmail.com'

# Ruta para el panel de administrador
@app.route('/admin')
def admin_panel():
    if not is_admin():
        return redirect('/')
    
    conn = get_db_connection()
    usuarios = conn.execute('SELECT * FROM usuarios').fetchall()
    conn.close()
    
    return render_template('admin.html', usuarios=usuarios)

# Ruta para editar usuario
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not is_admin():
        return redirect('/')
    
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        nueva_contraseña = request.form['nueva_contraseña']
        
        if nueva_contraseña:
            hashed_password = hash_password(nueva_contraseña)
            conn.execute('UPDATE usuarios SET nombre = ?, correo = ?, contraseña = ? WHERE id = ?',
                         (nombre, correo, hashed_password, user_id))
        else:
            conn.execute('UPDATE usuarios SET nombre = ?, correo = ? WHERE id = ?',
                         (nombre, correo, user_id))
        
        conn.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect('/admin')
    
    conn.close()
    return render_template('edit_user.html', usuario=usuario)

if __name__ == '__main__':
    app.run(debug=True)