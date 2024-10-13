
    from flask import Flask, request, jsonify, render_template, redirect, url_for, session
    import fitz  # PyMuPDF
    import os
    from werkzeug.utils import secure_filename
    from transformers import pipeline

    app = Flask(__name__)
    app.secret_key = 'supersecretkey'  # Used for session management

    # Admin password for accessing the backend
    ADMIN_PASSWORD = 'admin123'

    # Folder to save uploaded PDFs
    UPLOAD_FOLDER = './uploaded_pdfs'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Load the NLP model for question-answering
    nlp = pipeline("question-answering")

    # Function to extract text from PDFs
    def extract_text_from_pdf(pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    # Store uploaded PDF content
    pdf_texts = {}

    @app.route('/')
    def chatbot():
        return render_template('chatbot_widget.html')

    # Admin login route
    @app.route('/admin', methods=['GET', 'POST'])
    def admin():
        if 'logged_in' in session and session['logged_in']:
            return render_template('admin.html')
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            password = request.form.get('password')
            if password == ADMIN_PASSWORD:
                session['logged_in'] = True
                return redirect(url_for('admin'))
            else:
                return "Incorrect password. Please try again.", 401
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        return redirect(url_for('login'))

    @app.route('/upload', methods=['POST'])
    def upload_pdf():
        if 'logged_in' not in session or not session.get('logged_in'):
            return redirect(url_for('login'))

        if 'pdf' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['pdf']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text from PDF and store it
        pdf_texts[filename] = extract_text_from_pdf(filepath)

        return jsonify({'message': 'PDF uploaded successfully'}), 200

    @app.route('/ask', methods=['POST'])
    def ask_question():
        data = request.json
        question = data.get('message')

        # Combine content from all PDFs and search for an answer
        combined_pdf_text = " ".join(pdf_texts.values())

        # Use NLP model to find an answer
        answer = nlp(question=question, context=combined_pdf_text)

        return jsonify({'response': answer['answer']}), 200

    if __name__ == '__main__':
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        app.run(debug=True)
    