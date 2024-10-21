import os
import pandas as pd
import hashlib
import sqlite3
from cryptography.fernet import Fernet

# Function to generate SHA-256 secret key
def generate_secret_key(file_content: str) -> str:
    sha_signature = hashlib.sha256(file_content.encode()).hexdigest()
    return sha_signature

# Function to encrypt the file using Fernet (symmetric encryption)
def encrypt_file(file_content: str, encryption_key: bytes) -> bytes:
    fernet = Fernet(encryption_key)
    encrypted_file = fernet.encrypt(file_content.encode())
    return encrypted_file

# Database setup (SQLite for simplicity)
def setup_database():
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_number TEXT,
            secret_key TEXT,
            encrypted_file BLOB
        )
    ''')
    conn.commit()
    return conn

# Function to store the secret key, hospital number, and encrypted file in the database
def store_in_database(conn, hospital_number: str, secret_key: str, encrypted_file: bytes):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO patient_files (hospital_number, secret_key, encrypted_file) VALUES (?, ?, ?)", 
                   (hospital_number, secret_key, encrypted_file))
    conn.commit()

# Generate file path based on hospital number (patient ID)
def get_file_path(hospital_number: str) -> str:
    return f"uploads/{hospital_number}.csv"

# Main processing function for individual patient files
def process_patient_file(hospital_number: str):
    # Ensure the processed uploads directory exists
    processed_folder = 'processed_uploads'
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

    file_path = get_file_path(hospital_number)  # Dynamically generate the file path based on the patient ID
    
    # Load CSV file for the patient (one patient per file)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='ISO-8859-1')

    # Ensure there's only one patient's data in the file
    if len(df) != 1:
        raise ValueError("CSV file must contain exactly one patient's data.")

    # Convert DataFrame to CSV string without secret key
    file_content = df.to_csv(index=False)
    
    # Generate a secret key based on the original file content
    secret_key = generate_secret_key(file_content)
    print(f"Generated Secret Key for {hospital_number}: {secret_key}")

    # Add the secret key as a new column in the DataFrame
    df['secret_key'] = secret_key

    # Save the updated CSV file back with the secret key
    df.to_csv(file_path, index=False)  # Overwrite original file with secret key added

    # Now encrypt the file content with the secret key included
    encryption_key = Fernet.generate_key()
    encrypted_file = encrypt_file(df.to_csv(index=False), encryption_key)
    
    print(f"File for {hospital_number} has been encrypted and secret key added to the file.")

    # Store hospital number, secret key, and encrypted file in database
    conn = setup_database()
    store_in_database(conn, hospital_number, secret_key, encrypted_file)
    print(f"Data for {hospital_number} stored in the database successfully.")

    # Save the encrypted file on disk in the "processed_uploads" folder
    encrypted_file_path = f"{processed_folder}/{hospital_number}_encrypted.csv"
    with open(encrypted_file_path, 'wb') as f:
        f.write(encrypted_file)
    
    print(f"Encrypted file saved to: {encrypted_file_path}")
    
    return encryption_key, secret_key, encrypted_file

# Function to validate an individual patient's file
def validate_existing_patient_file(hospital_number: str):
    file_path = get_file_path(hospital_number)  # Dynamically generate the file path based on the patient ID
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='ISO-8859-1')

    # Ensure there's only one patient's data in the file
    if len(df) != 1:
        raise ValueError("CSV file must contain exactly one patient's data.")

    # Extract the secret key stored in the file
    stored_secret_key = df['secret_key'].iloc[0]  # Since there's only one row, take the first secret key
    
    # Generate the secret key based on the file's content (excluding the 'secret_key' column)
    file_content = df.drop(columns=['secret_key']).to_csv(index=False)
    generated_secret_key = generate_secret_key(file_content)

    # Check if the generated key matches the stored secret key
    if stored_secret_key == generated_secret_key:
        print(f"The file for hospital number {hospital_number} was validated successfully.")
    else:
        print(f"The file for hospital number {hospital_number} has been modified or is not recognized.")
