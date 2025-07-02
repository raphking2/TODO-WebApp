import os
from flask import Flask, jsonify, render_template, url_for, request, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

#Additional Test
import fitz  # PyMuPDF
import docx
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Prevents warnings
db = SQLAlchemy(app)



# Initialize Flask-Migrate
migrate = Migrate(app, db)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200),nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id


# Create the database tables
with app.app_context():
    db.create_all()



@app.route('/',methods=['POST','GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        #if not task_content.strip():
            #flash('Can not accept an empty value into the database')
            #return 'Can not accept an empty value into the database'
        new_task = Todo(content = task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue saving your task'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html',tasks=tasks)


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was issue deleting the task'

@app.route('/update/<int:id>',methods=['GET','POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was issue updating the task'

    else:
        return render_template('update.html',task=task)




@app.route('/parse-cv', methods=['POST'])
def parse_cv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', filename)
        file.save(temp_path)

        try:
            if filename.lower().endswith('.pdf'):
                extracted_text = extract_text_from_pdf(temp_path)
            elif filename.lower().endswith('.docx'):
                extracted_text = extract_text_from_docx(temp_path)
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

            os.remove(temp_path)
            return jsonify({'text': extracted_text})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400



if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)