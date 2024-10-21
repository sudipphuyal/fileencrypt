from flask import Flask, request, render_template, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from main import process_patient_file, validate_existing_patient_file

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Route for the file upload form
@app.route('/')
def upload_file():
    return render_template('upload.html')

# Route for handling file upload and processing
@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        # Secure the filename
        filename = secure_filename(file.filename)

        # Ensure the file has a .csv extension
        if not filename.endswith('.csv'):
            flash('Only CSV files are allowed')
            return redirect(request.url)

        # Save the uploaded file to the upload folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract hospital number from filename (remove the .csv extension)
        hospital_number = os.path.splitext(filename)[0]

        # Process the uploaded file with the backend function
        process_patient_file(hospital_number)  # Pass the hospital number extracted from the filename
        flash(f'File processed successfully for hospital number: {hospital_number}')
        return redirect(url_for('upload_file'))

# Route for validating an uploaded file
@app.route('/validate', methods=['POST'])
def validate_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        # Secure the filename
        filename = secure_filename(file.filename)

        # Ensure the file has a .csv extension
        if not filename.endswith('.csv'):
            flash('Only CSV files are allowed')
            return redirect(request.url)

        # Save the uploaded file to the upload folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract hospital number from filename (remove the .csv extension)
        hospital_number = os.path.splitext(filename)[0]

        # Validate the uploaded file with the backend function
        validate_existing_patient_file(hospital_number)  # Pass the hospital number extracted from the filename
        flash(f'File validation complete for hospital number: {hospital_number}')
        return redirect(url_for('upload_file'))

if __name__ == "__main__":
    app.run(debug=True)
