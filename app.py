from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
# Import the connection error type for specific handling
from pymysql import err as pymysql_errors
from db_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Tell Flask to look for templates in the same folder ('.') instead of 'templates/'
# This assumes index.html is in the same directory as app.py.
app = Flask(__name__, template_folder='./templates') 
# NOTE: I am reverting this back to the standard './templates' path 
# because your screenshot shows the file is correctly placed in a 'templates' folder.
# If you confirm you still want it in the root directory, change it back to template_folder='.'

# IMPORTANT: Set a secret key for session management (needed for flash messages)
app.secret_key = 'super-secret-key-12345' 

def get_db_connection():
    """Attempts to establish a connection to the MySQL database."""
    # Use the RDS endpoint from the config file 
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

@app.route('/')
def index():
    feedbacks = []
    error_message = None
    conn = None

    try:
        # Attempt to get connection
        conn = get_db_connection()
        
        # If connection is successful, execute the query
        with conn.cursor() as cursor:
            cursor.execute("SELECT author, comment, created_at FROM feedback ORDER BY created_at DESC")
            feedbacks = cursor.fetchall()
    
    # Catch specific MySQL connection and operational errors
    except pymysql_errors.OperationalError as e:
        # If the database is unreachable, log the error and set an error message for the frontend
        print(f"Database connection or operation failed: {e}")
        error_message = "Error: Could not connect to the database. Please ensure the RDS instance is running and accessible (check security group)."
    except Exception as e:
        # Catch any other unexpected error
        print(f"An unexpected error occurred: {e}")
        error_message = f"An unexpected error occurred: {e}"
        
    finally:
        # Ensure connection is closed whether successful or not
        if conn and conn.open:
            conn.close()

    # Pass both feedback data and any error message to the template
    # The 'index.html' needs to be updated to display this 'error' variable.
    return render_template('index.html', feedbacks=feedbacks, error=error_message)

@app.route('/submit', methods=['POST'])
def submit():
    author = request.form['author']
    comment = request.form['comment']
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Insert the new comment into the RDBMS table
            sql = "INSERT INTO feedback (author, comment) VALUES (%s, %s)"
            cursor.execute(sql, (author, comment))
        conn.commit()
        flash("Feedback successfully submitted!", 'success')
    except pymysql_errors.OperationalError:
        # Flash a message if the database connection failed during submit
        flash("Could not post feedback: Database connection failed.", 'error')
    except Exception as e:
        flash(f"Error submitting feedback: {e}", 'error')
    finally:
        if conn and conn.open:
            conn.close()
            
    # Redirect back to the index page to see the new feedback (or error message)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
