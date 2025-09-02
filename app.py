import os
import tempfile
from flask import Flask, jsonify, render_template, url_for, request, redirect, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
import io
import base64

# Import data visualization packages with error handling
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: Plotly/Pandas not available. Chart generation will be disabled.")

# Import file processing packages with error handling
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available. PDF processing will be disabled.")

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. DOCX processing will be disabled.")

from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF is not available")
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_path):
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx is not available")
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
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
        # Use a cross-platform temporary directory
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
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
    

@app.route('/generate-charts', methods=['POST'])
def generate_charts():
    if not PLOTLY_AVAILABLE:
        return jsonify({'error': 'Chart generation is not available. Plotly/Pandas not installed.'}), 503
    
    try:
        data = request.get_json()
        
        if not data or 'visualizations' not in data:
            return jsonify({'error': 'Invalid data format'}), 400

        # Example: Net Profit by Branch
        profit_data = data['visualizations'][0]['data_series']
        df_profit = pd.DataFrame(profit_data)

        fig = px.bar(df_profit, x='branch', y='net_profit', title='Net Profit by Branch')
        
        # Use HTML instead of image for better compatibility
        chart_html = fig.to_html(include_plotlyjs='cdn')

        return jsonify({
            "chart_type": "bar",
            "title": "Net Profit by Branch",
            "chart_html": chart_html
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)