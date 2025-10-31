import mysql.connector
from mysql.connector import Error
from app.config.settings import settings

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=settings.DB_PORT
        )
        if connection.is_connected():
            print("✅ MySQL Database connected successfully!")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None
