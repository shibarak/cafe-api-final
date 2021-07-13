from flask import Flask, jsonify, render_template, request, abort, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlite3 import IntegrityError
from flask_bootstrap import Bootstrap
from random import *
import config
from wtforms import StringField, SubmitField, SelectField, PasswordField
from flask_wtf import FlaskForm
from wtforms.validators import *
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
import email_validator
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sQjbGSuTbd6o1tjBJkgq'
Bootstrap(app)
##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##Cafe TABLE Configuration
class Cafe(db.Model):
    __tablename__ = "cafe"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

## DB for API keys


class Keys(db.Model):
    __tablename__ = "API_keys"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    key = db.Column(db.String(200), nullable=False)


# db.create_all()
## form for API key

class KeyForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generatekey", methods=["GET", "POST"])
def generate_key():
    form = KeyForm()
    if form.validate_on_submit():
        alphabet = string.digits + string.ascii_letters
        key = ''.join(secrets.choice(alphabet)for i in range(12))
        email = form.email.data
        if Keys.query.filter_by(email=email).first():
            flash("An account is already registered with this email address.")
            return render_template("generatekey.html", form=form)
        new_key = Keys(key=key,
                       email=email)
        db.session.add(new_key)
        db.session.commit()
        return render_template("generatekey.html", success=True, key=key)
    return render_template("generatekey.html", form=form)

@app.route("/random", methods=["GET"])
def random():
    if Keys.query.filter_by(key=request.headers["Key"]).first():
        cafes = db.session.query(Cafe).all()
        random_cafe = choice(cafes)
        cafe_json = jsonify(cafe=random_cafe.to_dict())
        return cafe_json
    else:
        return abort(401)


@app.route("/all", methods=["GET"])
def get_all():
    if Keys.query.filter_by(key=request.headers["Key"]).first():
        cafes = db.session.query(Cafe).all()
        cafe_dicts = [cafe.to_dict() for cafe in cafes]
        return jsonify(cafes=cafe_dicts)
    else:
        return abort(401)

@app.route("/search", methods=["GET"])
def search():
    if Keys.query.filter_by(key=request.headers["Key"]).first():
        cafes = db.session.query(Cafe).all()
        results = []
        if "loc" in request.args:
            loc = request.args["loc"]
        else:
            return jsonify(error={"no_data": "Please provide a location"})

        for cafe in cafes:
            if cafe.location.lower() == loc.lower():
                results.append(cafe.to_dict())

        if not results:
            return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location"})
        else:
            return jsonify(cafes=results)
    else:
        return abort(401)
@app.route("/add", methods=["POST"])
def add_cafe():
    if request.method == "POST":
        if Keys.query.filter_by(key=request.headers["Key"]).first():
            d = request.form.to_dict()
            name = d["name"]
            map_url = d["map_url"]
            img_url = d["image_url"]
            location = d["location"]
            seats = d["seats"]
            has_toilet = bool(int(d["has_toilets"]))
            has_wifi = bool(int(d["has_wifi"]))
            has_sockets = bool(int(d["has_sockets"]))
            can_take_calls = bool(int(d["can_take_calls"]))
            coffee_price = d["coffee_price"]

            new_cafe = Cafe(name=name,
                            map_url=map_url,
                            img_url=img_url,
                            location=location,
                            seats=seats,
                            has_toilet=has_toilet,
                            has_wifi=has_wifi,
                            has_sockets=has_sockets,
                            can_take_calls=can_take_calls,
                            coffee_price=coffee_price)
            db.session.add(new_cafe)
            db.session.commit()
            return jsonify(response={"Success": "Successfully added the new cafe."})
        else:
            return abort(401)

@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def patch(cafe_id):
    if request.method == "PATCH":
        if Keys.query.filter_by(key=request.headers["Key"]).first():
            try:
                cafe = Cafe.query.get(cafe_id)
                cafe.coffee_price = request.args.get("new_price")
                db.session.commit()
                return jsonify(response={"Success": "The price has been successfully updated."}), 200
            except AttributeError:
                return jsonify(error={"Not Found": "No cafe with that id was found in the database"}), 404
        else:
            return abort(401)


@app.route("/delete/<int:cafe_id>", methods=["DELETE"])
def delete(cafe_id):
    if request.method == "DELETE":
        if Keys.query.filter_by(key=request.headers["Key"]).first():
            cafe = Cafe.query.get(cafe_id)
            if cafe:
                db.session.delete(cafe)
                db.session.commit()
                return jsonify(Success="Cafe successfully deleted."), 200
            else:
                return jsonify(error={"Not Found": "No cafe with that id was found in the database"}), 404
        else:
            return abort(401)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
