from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toko_buku.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model Buku
class Buku(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)
    harga = db.Column(db.Float, nullable=False)
    stok = db.Column(db.Integer, nullable=False)

# Model Admin
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    
    query = Buku.query
    if search_query:
        query = query.filter(Buku.nama.ilike(f'%{search_query}%'))
    
    books = query.paginate(page=page, per_page=5, error_out=False)
    return render_template('index.html', books=books.items, pagination=books, search_query=search_query)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nama = request.form['nama']
        harga = float(request.form['harga'])
        stok = int(request.form['stok'])
        
        book = Buku(nama=nama, harga=harga, stok=stok)
        db.session.add(book)
        db.session.commit()
        flash('Buku berhasil ditambahkan!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    book = Buku.query.get_or_404(book_id)

    if request.method == 'POST':
        book.nama = request.form['nama']
        book.harga = float(request.form['harga'])
        book.stok = int(request.form['stok'])
        
        db.session.commit()
        flash('Buku berhasil diperbarui!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    book = Buku.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Buku berhasil dihapus!', 'danger')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if Admin.query.filter_by(username=username).first():
            flash('Username sudah terdaftar. Silakan pilih username lain.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = Admin(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()
        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()

        if admin:
            if check_password_hash(admin.password, password):
                session['admin'] = admin.username
                flash('Login berhasil!', 'success')
                return redirect(url_for('index'))
        
        flash('Username atau password salah!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logout berhasil!', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
