import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from functools import wraps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# --- MySQL Configuration ---
MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
MYSQL_USER = os.getenv('DB_USER', 'root')
MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
MYSQL_DB = os.getenv('DB_NAME', 'boxoffice_db')

# --- Database Setup & Helper Functions ---

def get_db():
    if 'db' not in g:
        try:
            # Connect to MySQL server
            connection = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
            )
            # Create DB if it doesn't exist (Handled by setup SCript ideally, but safety check)
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
                cursor.execute(f"USE {MYSQL_DB}")
            
            # Select the DB
            connection.select_db(MYSQL_DB)
            g.db = connection
        except Exception as e:
             g.db_error = str(e) # Store error
             print(f"Error connecting to database: {e}")
             return None
            
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        try:
            db = get_db()
            if db is None:
                print("Could not connect to database setup.")
                return

            with db.cursor() as cursor:
                # Create Users Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL
                    )
                ''')

                # Create Movies Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS movies (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        genre VARCHAR(255) NOT NULL,
                        duration INT NOT NULL
                    )
                ''')

                # Create Bookings Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bookings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        movie_title VARCHAR(255) NOT NULL,
                        booking_date DATE NOT NULL,
                        tickets INT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')

                # Seed initial users if not exist
                cursor.execute("SELECT * FROM users WHERE username = %s", ('admin',))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", ('admin', 'admin123', 'Admin'))
                
                cursor.execute("SELECT * FROM users WHERE username = %s", ('tech',))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", ('tech', 'tech123', 'Tech Admin'))
                    
                cursor.execute("SELECT * FROM users WHERE username = %s", ('user',))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", ('user', 'user123', 'Customer'))
            
            db.commit()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Database initialization error: {e}")

# Initialize DB on first run logic should be handled carefully. 
# We'll call it, but if MySQL isn't running it will print an error.
init_db()

# --- Authentication Decorators ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                return "Access Denied: You do not have permission to view this page.", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'Tech Admin':
            return redirect(url_for('tech_admin_dashboard'))
        else:
            return redirect(url_for('customer_home'))
    return redirect(url_for('login'))

# Login / Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        db = get_db()
        if db:
            with db.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s AND role = %s", (username, role))
                user = cursor.fetchone()
                
                if user and user['password'] == password:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    
                    if role == 'Admin':
                        return redirect(url_for('admin_dashboard'))
                    elif role == 'Tech Admin':
                        return redirect(url_for('tech_admin_dashboard'))
                    else:
                        return redirect(url_for('customer_home'))
                else:
                    return render_template('login.html', error="Invalid credentials")
        else:
             error_msg = getattr(g, 'db_error', 'Unknown database connection error')
             return f"Database connection failed: {error_msg}", 500
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Admin Routes ---

@app.route('/admin/dashboard')
@login_required
@role_required('Admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/add_movie', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        duration = request.form['duration']
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO movies (title, genre, duration) VALUES (%s, %s, %s)", (title, genre, duration))
        db.commit()
        return redirect(url_for('view_movies'))
        
    return render_template('admin/add_movie.html')

@app.route('/admin/view_movies')
@login_required
@role_required('Admin')
def view_movies():
    db = get_db()
    movies = []
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM movies")
        movies = cursor.fetchall()
    return render_template('admin/view_movies.html', movies=movies)

# --- Tech Admin Routes ---

@app.route('/tech_admin/dashboard')
@login_required
@role_required('Tech Admin')
def tech_admin_dashboard():
    return render_template('tech_admin/dashboard.html')

@app.route('/tech_admin/change_password', methods=['GET', 'POST'])
@login_required
@role_required('Tech Admin')
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        user_id = session['user_id']
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, user_id))
        db.commit()
        return "Password changed successfully! <a href='/tech_admin/dashboard'>Back to Dashboard</a>"
        
    return render_template('tech_admin/change_password.html')

# --- Customer Routes ---

@app.route('/customer/home')
@login_required
@role_required('Customer')
def customer_home():
    db = get_db()
    movies = []
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM movies")
        movies = cursor.fetchall()
    return render_template('customer/home.html', movies=movies)

@app.route('/customer/booking', methods=['GET', 'POST'])
@login_required
@role_required('Customer')
def customer_booking():
    db = get_db()
    if request.method == 'POST':
        movie_title = request.form['movie_title']
        date = request.form['date']
        tickets = request.form['tickets']
        user_id = session['user_id']
        
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO bookings (user_id, movie_title, booking_date, tickets) VALUES (%s, %s, %s, %s)",
                       (user_id, movie_title, date, tickets))
        db.commit()
        return redirect(url_for('customer_history'))
    
    movies = []
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM movies")
        movies = cursor.fetchall()
    return render_template('customer/booking.html', movies=movies)

@app.route('/customer/history')
@login_required
@role_required('Customer')
def customer_history():
    user_id = session['user_id']
    db = get_db()
    bookings = []
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM bookings WHERE user_id = %s", (user_id,))
        bookings = cursor.fetchall()
    return render_template('customer/history.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True)
