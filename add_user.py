import mysql.connector
import bcrypt
import toml

def hash_password(password):
    """Hashes the password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def add_user_to_db():
    """Adds a new user to the database with a hashed password."""
    try:
        # Load database credentials from the secrets.toml file
        secrets = toml.load(".streamlit/secrets.toml")
        db_config = secrets["database"]

        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["db_name"],
            port=db_config["port"]
        )
        cursor = conn.cursor()

        print("--- Create a new user ---")
        username = input("Enter username: ")
        password = input("Enter password: ")

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print("Error: This username already exists. Please choose another one.")
            return

        # Hash the password and insert the new user
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()

        print(f"\nUser '{username}' was successfully created!")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    except FileNotFoundError:
        print("Error: `.streamlit/secrets.toml` not found. Please create it with your DB credentials.")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    add_user_to_db()
