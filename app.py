from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_file
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
import io

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Replace with a secure key

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'cadastro_gov'
}

# Function to connect to the database
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Generate PDF
def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Formulário de Cadastro", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Informações Pessoais", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Nome Completo: {data['nome']}", ln=True)
    pdf.cell(0, 10, f"Idade: {data['idade']}", ln=True)
    pdf.cell(0, 10, f"Gênero: {data['genero']}", ln=True)
    pdf.cell(0, 10, f"CPF: {data['cpf']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Contato", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"E-mail: {data['email']}", ln=True)
    pdf.cell(0, 10, f"Telefone: {data['telefone']}", ln=True)
    pdf.cell(0, 10, f"Endereço: {data['endereco']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Informações Financeiras", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Renda Familiar Mensal: R${data['renda']}", ln=True)
    pdf.cell(0, 10, f"Despesas Mensais: R${data['despesas']}", ln=True)
    pdf.cell(0, 10, f"Número de Membros da Família: {data['membros']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Escolaridade", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Nível de Escolaridade: {data['escolaridade']}", ln=True)
    
    if data.get('outros'):
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Outras Informações", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, data['outros'])
    
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# Home route
@app.route('/')
def index():
    return render_template('login.html')

# User login API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.form
    email = data['email']
    password = data['password']

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cadastro_login WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['senha'], password):
            flash('Login bem-sucedido!', 'success')
            return jsonify({'message': 'Login successful', 'redirect': url_for('cadastro_pessoa')})
        else:
            flash('Email ou senha incorretos.', 'error')
            return jsonify({'error': 'Invalid email or password'}), 401

    except mysql.connector.Error as err:
        flash(f'Erro: {err}', 'error')
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# User registration API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.form
    nome_completo = data['name']
    email = data['email']
    password = data['password']
    confirm_password = data['confirm-password']

    if password != confirm_password:
        flash('As senhas não coincidem.', 'error')
        return jsonify({'error': 'Passwords do not match'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cadastro_login (nome_completo, email, senha) VALUES (%s, %s, %s)",
            (nome_completo, email, hashed_password)
        )
        conn.commit()
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return jsonify({'message': 'Registration successful', 'redirect': url_for('index')})
    except mysql.connector.Error as err:
        flash(f'Erro: {err}', 'error')
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Person registration form
@app.route('/cadastro_pessoa')
def cadastro_pessoa():
    return render_template('cadastro_pessoa.html')

# Person registration API with PDF generation
@app.route('/api/cadastro', methods=['POST'])
def cadastro():
    data = request.form.to_dict()
    required_fields = ['nome', 'idade', 'genero', 'endereco', 'cpf', 'email', 'telefone', 'renda', 'membros', 'despesas', 'escolaridade']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cadastro_pessoas (
                nome_completo, idade, genero, endereco_completo, cpf, email, telefone,
                renda_familiar_mensal, numero_membros_familia, despesas_mensais,
                nivel_escolaridade, outras_informacoes, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data['nome'], data['idade'], data['genero'], data['endereco'], data['cpf'], data['email'],
                data['telefone'], data['renda'], data['membros'], data['despesas'], data['escolaridade'],
                data.get('outros', ''), 'Pendente'
            )
        )
        conn.commit()

        # Generate PDF
        pdf_buffer = generate_pdf(data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"cadastro_{data['cpf']}.pdf"
        )

    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Admin login page
@app.route('/admin')
def admin():
    return render_template('admin_login.html')

# Admin login API
@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    data = request.form
    nome = data['email']  # Using email as nome for consistency with form
    senha = data['password']

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM login_adm WHERE nome = %s", (nome,))
        admin = cursor.fetchone()

        if admin and check_password_hash(admin['senha'], senha):
            flash('Login de administrador bem-sucedido!', 'success')
            return jsonify({'message': 'Admin login successful', 'redirect': url_for('admin_dashboard')})
        else:
            flash('Nome ou senha incorretos.', 'error')
            return jsonify({'error': 'Invalid admin credentials'}), 401

    except mysql.connector.Error as err:
        flash(f'Erro: {err}', 'error')
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# API to fetch all registrations
@app.route('/api/registrations', methods=['GET'])
def get_registrations():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome_completo, cpf, endereco_completo, status FROM cadastro_pessoas")
        registrations = cursor.fetchall()
        
        # Extract city from endereco_completo (assuming format includes city)
        for reg in registrations:
            city = reg['endereco_completo'].split(',')[-2].strip() if ',' in reg['endereco_completo'] else 'Unknown'
            reg['city'] = city
        
        return jsonify(registrations)
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# API to update registration status
@app.route('/api/registrations/<int:id>/status', methods=['PUT'])
def update_registration_status(id):
    data = request.json
    status = data.get('status')

    if status not in ['Pendente', 'Aprovado', 'Rejeitado']:
        return jsonify({'error': 'Invalid status'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE cadastro_pessoas SET status = %s WHERE id = %s",
            (status, id)
        )
        conn.commit()
        return jsonify({'message': 'Status updated successfully'})
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# API to edit registration
@app.route('/api/registrations/<int:id>', methods=['PUT'])
def edit_registration(id):
    data = request.json
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE cadastro_pessoas SET
                nome_completo = %s, idade = %s, genero = %s, endereco_completo = %s,
                cpf = %s, email = %s, telefone = %s, renda_familiar_mensal = %s,
                numero_membros_familia = %s, despesas_mensais = %s, nivel_escolaridade = %s,
                outras_informacoes = %s
            WHERE id = %s
            """,
            (
                data['nome_completo'], data['idade'], data['genero'], data['endereco_completo'],
                data['cpf'], data['email'], data['telefone'], data['renda_familiar_mensal'],
                data['numero_membros_familia'], data['despesas_mensais'], data['nivel_escolaridade'],
                data.get('outras_informacoes', ''), id
            )
        )
        conn.commit()
        return jsonify({'message': 'Registration updated successfully'})
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# API to delete registration
@app.route('/api/registrations/<int:id>', methods=['DELETE'])
def delete_registration(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cadastro_pessoas WHERE id = %s", (id,))
        conn.commit()
        return jsonify({'message': 'Registration deleted successfully'})
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)