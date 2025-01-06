from flask import Flask, render_template, url_for, request, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
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



if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)