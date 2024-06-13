from flask import Flask, render_template, redirect, url_for, request, session, g, flash, send_from_directory, abort
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'swengineering'
DATABASE = 'database.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_username(user_id):
    user = query_db('SELECT username FROM users WHERE id = ?', [user_id], one=True)
    return user[0] if user else 'Unknown'

@app.template_filter('get_username')
def get_username_filter(user_id):
    return get_username(user_id)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        flash('Invalid credentials')
    users = query_db('SELECT * FROM users')
    photos = query_db('SELECT photos.*, users.username FROM photos JOIN users ON photos.user_id = users.id')
    return render_template('index.html', users=users, photos=photos)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        db = get_db()
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', [username, password])
        db.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user = query_db('SELECT * FROM users WHERE id = ?', [session['user_id']], one=True)
        photos = query_db('SELECT * FROM photos WHERE user_id = ?', [session['user_id']])
        return render_template('profile.html', user=user, photos=photos)
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' in session:
        if request.method == 'POST':
            description = request.form['description']
            keyword = request.form['keyword']
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                db = get_db()
                db.execute('INSERT INTO photos (user_id, description, keyword, filename) VALUES (?, ?, ?, ?)', 
                          [session['user_id'], description, keyword, filename])
                db.commit()
                return redirect(url_for('profile'))
            flash('Invalid file format')
        return render_template('upload.html')
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    if 'user_id' not in session:
        abort(401)
    user_id = session['user_id']
    photo = query_db('SELECT * FROM photos WHERE id = ? AND user_id = ?', [photo_id, user_id], one=True)
    if not photo:
        abort(403)
    db = get_db()
    db.execute('DELETE FROM photos WHERE id = ?', [photo_id])
    db.commit()
    filename = photo[4]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('사진이 삭제되었습니다.')
    else:
        flash('파일이 이미 삭제되었거나 존재하지 않습니다.')
    return redirect(url_for('profile'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        # keyword 양쪽에 % 와일드카드 추가
        photos = query_db('SELECT * FROM photos WHERE keyword LIKE ?', ['%' + keyword + '%'])
        return render_template('search.html', photos=photos)
    return render_template('search.html')


@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' in session:
        recipient_id = request.args.get('recipient_id')
        if request.method == 'POST':
            recipient_id = request.form['recipient_id']
            message = request.form['message']
            db = get_db()
            db.execute('INSERT INTO messages (sender_id, recipient_id, message) VALUES (?, ?, ?)', 
                      [session['user_id'], recipient_id, message])
            db.commit()
        
        if recipient_id:
            user_messages = query_db(
                'SELECT * FROM messages WHERE (sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?) ORDER BY id',
                [session['user_id'], recipient_id, recipient_id, session['user_id']]
            )
        else:
            user_messages = []
        
        users = query_db('SELECT id, username FROM users WHERE id != ?', [session['user_id']])

        return render_template('messages.html', messages=user_messages, users=users, recipient_id=recipient_id)
    return redirect(url_for('index'))

@app.route('/edit_photo/<int:photo_id>', methods=['GET', 'POST'])
def edit_photo(photo_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    db = get_db()
    photo = db.execute('SELECT * FROM photos WHERE id = ?', [photo_id]).fetchone()
    if not photo:
        abort(404) 

    if request.method == 'POST':
        description = request.form['description']
        keyword = request.form['keyword']
        file = request.files['file']
        filename = photo[4]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.execute('UPDATE photos SET description = ?, keyword = ?, filename = ? WHERE id = ?',
                  [description, keyword, filename, photo_id])
        db.commit()
        flash('사진이 수정되었습니다.')
        return redirect(url_for('profile'))

    return render_template('edit_photo.html', photo=photo)

@app.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if 'user_id' not in session:
        abort(401)

    user_id = session['user_id']
    message = query_db('SELECT * FROM messages WHERE id = ? AND sender_id = ?', [message_id, user_id], one=True)
    if not message:
        abort(403) 
    db = get_db()
    db.execute('DELETE FROM messages WHERE id = ?', [message_id])
    db.commit()
    recipient_id = request.args.get('recipient_id')
    if recipient_id:
        return redirect(url_for('messages', recipient_id=recipient_id))
    else:
        return redirect(url_for('messages'))



if __name__ == '__main__':
    app.run(debug=True)
