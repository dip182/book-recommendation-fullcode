from flask import Flask, render_template, request, session, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from flask import send_file
from sklearn.metrics.pairwise import cosine_similarity
from flask_login import login_required
from flask import render_template
import mysql.connector
import pickle
import numpy as np
import pandas as pd
from flask import jsonify

app = Flask(__name__, static_url_path='/static')

app = Flask(__name__)
app.secret_key = 'hello'  # Replace with a random secret key

# Initialize Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

...
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
app.config['THEME'] = 'light'  # Initialize the theme as 'light'
...

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))

@app.route('/toggle_theme')
def toggle_theme():
    if 'THEME' not in session:
        session['THEME'] = 'light'
    else:
        if session['THEME'] == 'light':
            session['THEME'] = 'dark'
        else:
            session['THEME'] = 'light'
    return redirect(request.referrer)

@app.route('/light theme')
def serve_light_theme():
    return send_file('templates/light theme.html')

@app.route('/book_recommendation')
def book_recommendation():
    return render_template('book_recommendation.html')

@app.route('/About Us')
def about_us():
    return send_file('templates/About Us.html')

@app.route('/example')
def example():
    data = {'key': 'value'}
    return jsonify(data)

# Define the User class
class User(UserMixin):
    def __init__(self, username):
        self.username = username

users = {
    'dip_karki': {'dip': 'dip'},
    'dip karki': {'dip': 'dip'}
}


# Tell Flask-Login how to load a user
@login_manager.user_loader
def load_user(username):
    return User(username)

@app.route('/')
def index():
    rounded_ratings = [round(rating, 1) for rating in list(popular_df['avg_ratings'].values)]
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-S'].values),
                           votes=list(popular_df['num_ratings'].values),
                           ratings=rounded_ratings
                           )
@app.route('/top_50_books')
def top_50_books():
    rounded_ratings = [round(rating, 1) for rating in list(popular_df['avg_ratings'].values)]
    return render_template('top_50_books.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-S'].values),
                           votes=list(popular_df['num_ratings'].values),
                           ratings=rounded_ratings
                           )

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')


@app.route('/recommend_books', methods=['post'])
def recommend_books():
    username = session.get('username')  # Get the username from the session
    user_input = request.form.get('user_input')

    # Check if user_input is in pt.index
    if user_input in pt.index:
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:6]

        data = []
        for i in similar_items:
            item = []
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

            data.append(item)

        return render_template('recommend.html', data=data, username=username)  # Pass the username to the template
    else:
        error_message = "Book not found. Please try again."
        return render_template('recommend.html', error_message=error_message, username=username)
def update_similarity_scores(user_ratings):
    pt = user_ratings.pivot_table(index='User-ID', columns='ISBN', values='Book-Rating').fillna(0)
    similarity_scores = cosine_similarity(pt)
    print(user_ratings.columns)
    return similarity_scores

@app.route('/')
def student():
    return render_template('login.html')


# Route for handling the login page
@app.route('/login', methods=['POST'])
def login_user_route():
    username = request.form['username']
    password = request.form['password']

    # Connect to the database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="book_recommendation_system"
    )

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM register WHERE username=%s AND password=%s", (username, password))
    r = mycursor.fetchall()
    count = mycursor.rowcount

    if count == 1:
        session['username'] = username  # Set session for logged-in user
        return render_template("recommend.html", welcome="Welcome,", username=username)  # Pass welcome message and username
    else:
        error = "Invalid Username or Password"
        return render_template("login.html", error=error)

    mydb.commit()
    mycursor.close()
    mydb.close()  # Close the connection

@app.route('/test')
def test():
        if 'username' in session:
            username = session['username']
            return render_template("recommend.html", username=username)
        else:
            return redirect('/login')  # Redirect to login if user is not logged in


# ... (other imports and route definitions)

# Route for handling the registration form
@app.route('/register', methods=['POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']  # Corrected variable name

        # Check if passwords match
        if password != confirm_password:
            return "Passwords do not match."

        # Connect to the database
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="book_recommendation_system"
        )
        mycursor = mydb.cursor()

        # Insert the user data into the database
        insert_query = "INSERT INTO register (username, email, password, confirm_password) VALUES (%s, %s, %s, %s)"
        user_data = (username, email, password, confirm_password)
        try:
            mycursor.execute(insert_query, user_data)
            mydb.commit()

            # Close the database connection
            mycursor.close()
            mydb.close()

            return jsonify({'success': True})  # Indicate success

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return jsonify({'success': False, 'message': 'Error occurred while submitting rating.'})

        else:
            return jsonify({'success': False, 'message': 'User not logged in.'})

@app.route('/delete_book', methods=['post'])
def delete_book():
    username = session.get('username')
    book_title = request.form['book_title']
    book_author = request.form['book_author']
    image_url = request.form['image_url']

    # Connect to the database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="book_recommendation_system"
    )
    mycursor = mydb.cursor()

    # Delete the book from the user's list
    delete_query = "DELETE FROM user_books WHERE username = %s AND book_title = %s AND book_author = %s AND image_url = %s"
    delete_data = (username, book_title, book_author, image_url)
    try:
        mycursor.execute(delete_query, delete_data)
        mydb.commit()

        return redirect(url_for('my_list'))

    except Exception as e:
        print(f"Error occurred: {e}")
        mydb.rollback()

    finally:
        # Close the database connection
        mycursor.close()
        mydb.close()

    return "Error occurred while deleting the book from the list."

@app.route('/submit_rating', methods=['post'])
def submit_rating():
    if 'username' in session:
        username = session['username']
        ISBN = request.form.get('ISBN')
        BookRating = request.form.get('BookRating')
        BookTitle = request.form.get('Book-Title')

        # Assuming you have other fields like image_url, user_rating, want_to_read, read_shelf

        # Connect to the database
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="book_recommendation_system"
        )
        mycursor = mydb.cursor()

        # Insert the rating into the ratings table
        insert_query = "INSERT INTO ratings (username, ISBN, `Book-Rating`,`Book-Title`) VALUES (%s, %s, %s,%s)"
        user_data = (username, ISBN, BookRating, BookTitle)
        try:
            mycursor.execute(insert_query, user_data)
            mydb.commit()

            # Close the database connection
            mycursor.close()
            mydb.close()

            # Render success message
            return render_template('success.html', message="Rating submitted successfully!")

        except mysql.connector.Error as err:
            # Handle the error
            print(f"Error: {err}")
            # Render error message
            return render_template('error.html', message="Error occurred while submitting rating.")

    else:
        return redirect('/login')  # Redirect to login if user is not logged in

@app.route('/recommend', methods=['post'])
def recommend():
    username = session.get('username')

    user_ratings = get_user_ratings(username)

    similarity_scores = update_similarity_scores(user_ratings)

    updated_data = []
    for i, item in enumerate(similar_items):
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        if pt.index[i[0]] not in user_ratings.index:
            updated_data.append(item)

    return render_template('recommend.html', data=updated_data, username=username)


@app.route('/signout')
def signout():
    # Clear the user's session (logout)
    session.clear()
    return redirect(url_for('login'))

@app.route('/add_to_my_list', methods=['POST'])
def add_to_my_list():
    username = request.form['username']
    book_title = request.form['book_title']
    book_author = request.form['book_author']
    image_url = request.form['image_url']

    print(f"Received request to add book: {book_title} by {book_author} for user: {username}")

    # Connect to the database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="book_recommendation_system"
    )
    mycursor = mydb.cursor()

    # Insert the book into the user's list
    insert_query = "INSERT INTO user_books (username, book_title, book_author, image_url) VALUES (%s, %s, %s, %s)"
    user_data = (username, book_title, book_author, image_url)
    try:
        mycursor.execute(insert_query, user_data)
        mydb.commit()

        return redirect(url_for('my_list'))

    except Exception as e:
        print(f"Error occurred: {e}")
        mydb.rollback()

    finally:
        # Close the database connection
        mycursor.close()
        mydb.close()

    return "Error occurred while adding the book to the list."

@app.route('/my_list')
def my_list():
    username = session.get('username')  # Get the username from the session

    # Connect to the database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="book_recommendation_system"
    )
    mycursor = mydb.cursor()

    # Retrieve the user's book list from the database
    mycursor.execute("SELECT book_title, book_author, image_url FROM user_books WHERE username = %s", (username,))
    user_book_list = mycursor.fetchall()

    # Close the database connection
    mycursor.close()
    mydb.close()

    return render_template('my_list.html', book_list=user_book_list, username=username)

def get_user_book_list(username):
    # Connect to the database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="book_recommendation_system"
    )
    mycursor = mydb.cursor()

    # Retrieve the user's book list from the database
    mycursor.execute("SELECT * FROM user_books WHERE username = %s", (username,))
    user_book_list = mycursor.fetchall()

    # Close the database connection
    mycursor.close()
    mydb.close()

    return user_book_list


def get_user_ratings(username):
    # Connect to the database
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="book_recommendation_system"
    )
    mycursor = mydb.cursor()

    # Retrieve the user's ratings from the database
    mycursor.execute("SELECT `User-ID`, ISBN, `Book-Rating` FROM ratings WHERE username = %s", (username,))
    user_ratings = mycursor.fetchall()

    # Close the database connection
    mycursor.close()
    mydb.close()

    user_ratings_df = pd.DataFrame(user_ratings, columns=['User-ID', 'ISBN', 'Book-Rating'])
    return user_ratings_df

if __name__ == '__main__':
    app.run(debug=True)
