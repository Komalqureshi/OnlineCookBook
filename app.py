from flask import Flask, render_template, request, redirect, flash
from flask_bootstrap import Bootstrap
from flaskext.mysql import MySQL
import yaml
app = Flask(__name__)
app.secret_key = "secret_key"  # set secret key in order for database to work

Bootstrap(app)  # including base bpptstrap from flask
mysql = MySQL(app)

# MySQL configurations
db = yaml.load(open('db.yaml'))  # getting database credentials stored in yaml file.
app.config['MYSQL_DATABASE_USER'] = db['mysql_user']
app.config['MYSQL_DATABASE_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DATABASE_DB'] = db['mysql_db']
app.config['MYSQL_DATABASE_HOST'] = db['mysql_host']
mysql.init_app(app)  # initiate mysql connection

if __name__ == '__main__':  #run the app if its the main activity
    app.run(debug=True)


@app.route('/course/<string:title>')  #filtyer recipes by Recipe Course
def get_recipe(title):
    conn = mysql.connect()  # start connection to mysql
    cur = conn.cursor()  # obtain a cursor of database
    total = cur.execute("SELECT * FROM recipe WHERE course = %s",
                        (title))  # filter recipes by recipe course from database
    if total > 0:  #if there are some recipes then fetch all of them and close the connection
        recipe = cur.fetchall()
        conn.close()
        return render_template('recipes.html', recipe=recipe)  #pass the data to template in order to render.
    else:
        return render_template('recipes.html',
                               recipe=None)  # if there are no recipes in that particular course pass None


@app.route('/dietry/<int:dietry>')  #filter recipes by dietry
def get_recipe_by_dietry(dietry):
    conn = mysql.connect()
    cur = conn.cursor()
    total = cur.execute("SELECT * FROM recipe r, recipe_dietry d WHERE d.recipe_id = r.id and d.dietry_id= %s ",
                        (dietry))  #filter recipes by dietry
    if total > 0:
        recipe = cur.fetchall()
        conn.close()
        return render_template('recipes.html', recipe=recipe, dietry_id=dietry)
    else:
        flash("No recipes found by this filter",'danger')
        return render_template('recipes.html', recipe=None)




@app.route('/')
def index():  #if its the main page, show all recipes.
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipe")
    recipes = cur.fetchall()
    conn.close()

    return render_template('index.html', recipe=recipes)


@app.route('/recipe/<int:recipe_id>')  #show single recipe
def show_recipe(recipe_id):
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("UPDATE recipe SET views = views+1 WHERE id = %s",
                (recipe_id))  #increase recipe view by 1 to count the view.
    conn.commit()

    cur.execute("SELECT * FROM recipe WHERE id = %s", (recipe_id))  #get the recipe and show it.
    recipe = cur.fetchone()
    conn.close()

    return render_template('recipe.html', recipe=recipe)


@app.route('/upvote/<int:recipe_id>')  #upvote a recipe
def upvote_recipe(recipe_id):
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("UPDATE recipe SET upvotes = upvotes+1 WHERE id = %s",
                (recipe_id))  #update vote in database for that particular recipe
    conn.commit()
    cur.execute("SELECT * FROM recipe WHERE id = %s", (recipe_id))
    recipe = cur.fetchone()
    conn.close()
    flash("Successfully Upvoted",'success')
    return render_template('recipe.html',recipe = recipe)


@app.route('/delete/<int:recipe_id>')
def delete_recipe(recipe_id):
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipe_dietry WHERE recipe_id = %s",
                (recipe_id))  #delete recipe dietry in database first to delete the recipe altogether
    conn.commit()
    cur.execute("DELETE FROM recipe WHERE id = %s", (recipe_id))  #delete recipe
    conn.commit()
    conn.close()
    flash("Successfully Deleted Recipe", 'success')
    return redirect('/')




@app.route('/submit',methods = ['GET','POST'])
def submit_recipe():
    if request.method == "POST":  # if method is post it means form is submitted and a new recipe needs to be added.
        form = request.form  #get form data
        title = form['title']
        ingredients = form['ingredients']
        instructions = form['instructions']
        authors = form['author']
        author_country = form['country']
        course = form['course']
        dietry = form.getlist('dietry')
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO recipe(title,ingredients,instructions,authors,author_country,course) VALUES(%s,%s,%s,%s,%s,%s)",(title, ingredients, instructions, authors, author_country, course))  #insert into database
        conn.commit()

        id = cur.lastrowid  #get the recently added recipe Id to add dietry values in dietry table
        for diet in dietry:
            cur.execute(
                "INSERT INTO recipe_dietry(recipe_id,dietry_id) VALUES(%s,%s)",
                (id, diet))
            conn.commit()

        conn.close()
        flash("Successfully Added", 'success')
        return redirect('/')

    else:
        return render_template('submit.html')


@app.route('/edit/<int:recipe_id>', methods=['GET','POST'])  #accepts get and post. Get for showing the edit menu of recipe and post to update the recipe
def edit_recipe(recipe_id):
    if request.method == "POST":  # update recipe
        form = request.form  #get new values from form
        title = form['title']
        ingredients = form['ingredients']
        instructions = form['instructions']
        authors = form['author']
        author_country = form['country']
        course = form['course']
        dietry = form.getlist('dietry')
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE recipe SET title = %s ,ingredients = %s ,instructions = %s, authors  = %s,author_country = %s,course = %s WHERE id= %s",
            (title, ingredients, instructions, authors, author_country, course, recipe_id))
        conn.commit()  # update recipe
        cur.execute("DELETE FROM recipe_dietry WHERE recipe_id = %s", (recipe_id))  #delete all dietry values in recipe_dietry to put in new set of selected values
        conn.commit()

        for diet in dietry:  #insert new dietry values
            cur.execute("INSERT INTO recipe_dietry(recipe_id,dietry_id) VALUES(%s,%s)",(recipe_id, diet))
            conn.commit()

        # show edit page of recipe with newly inserted values

        total = cur.execute("SELECT * FROM recipe where id = %s", (recipe_id))  #get the recipe with updated values
        if total > 0:
            recipe = cur.fetchone()
            total = cur.execute("SELECT * FROM recipe_dietry where recipe_id = %s",(recipe_id))  # get recipe dietry values
            if total > 0:
                dietry = cur.fetchall()
                di = ""
                for diet in dietry:  #join the dietry values in single string to pass to jinja template in multiple select field
                    di += str(diet[2])
                    di += ","
                flash("Successfully Updated", 'success')
                return render_template('edit.html', recipe=recipe, dietry_se=di)
            else:
                flash("Error Updating Recipe", 'danger')
                return render_template('edit.html', recipe=recipe, dietry_sel="None")
        conn.close()
    else:
        # show edit page of recipe
        conn = mysql.connect()
        cur = conn.cursor()
        total = cur.execute("SELECT * FROM recipe where id = %s", (recipe_id))  #get recipe
        if total > 0:
            recipe = cur.fetchone()
            total = cur.execute("SELECT * FROM recipe_dietry where recipe_id = %s", (recipe_id))  #get recipe dietry values
            if total > 0:
                dietry = cur.fetchall()
                di = ""
                for diet in dietry:
                    di += str(diet[2])
                    di += ","

                return render_template('edit.html',recipe = recipe, dietry_se = di)
            else:
                return render_template('edit.html', recipe=recipe, dietry_sel="None")
