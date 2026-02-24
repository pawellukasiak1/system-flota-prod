
from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# ====== KONFIGURACJA BAZY ======
database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ====== MODELE ======
class Pojazd(db.Model):
    __tablename__ = "pojazdy"

    id = db.Column(db.Integer, primary_key=True)
    nr_rejestracyjny = db.Column(db.String(50))
    vin = db.Column(db.String(100))
    marka = db.Column(db.String(100))
    model = db.Column(db.String(100))
    rok = db.Column(db.Integer)
    badanie_techniczne = db.Column(db.String(20))
    oc = db.Column(db.String(20))
    tacho = db.Column(db.String(20))

    serwisy = db.relationship("Serwis", backref="pojazd", cascade="all, delete")

class Serwis(db.Model):
    __tablename__ = "serwis"

    id = db.Column(db.Integer, primary_key=True)
    pojazd_id = db.Column(db.Integer, db.ForeignKey("pojazdy.id"))
    data = db.Column(db.String(20))
    opis = db.Column(db.Text)
    przebieg = db.Column(db.Integer)
    koszt = db.Column(db.Float)

with app.app_context():
    db.create_all()

# ====== STYL ======
STYLE = """
<style>
body { font-family: Arial; background:#f4f6f9; margin:0; }
.btn-red { background-color: red; color: white; }
.header { background:#1f2937; color:white; padding:20px; }
.container { padding:30px; }
table { width:100%; border-collapse: collapse; background:white; }
th, td { padding:12px; border-bottom:1px solid #ddd; text-align:left; }
th { background:#111827; color:white; }
tr:hover { background:#f1f1f1; }
.btn { padding:6px 12px; text-decoration:none; border-radius:6px; font-size:14px; }
.btn-blue { background:#2563eb; color:white; }
.btn-green { background:#16a34a; color:white; }
.btn-orange { background:#ea580c; color:white; }
form input, form textarea { padding:8px; margin-bottom:10px; width:300px; }
form button { padding:10px 20px; background:#2563eb; color:white; border:none; border-radius:6px; }
</style>
"""

# ====== KOLOR DAT ======
def kolor_daty(data):
    if not data:
        return "-", ""

    try:
        dzis = datetime.today().date()
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        roznica = (data_obj - dzis).days

        if roznica <= 9:
            return data, "background-color:#fecaca;"
        elif 10 <= roznica <= 30:
            return data, "background-color:#fef08a;"
        else:
            return data, ""
    except:
        return data, ""

# ====== STRONA GŁÓWNA ======
@app.route("/")
def index():
    pojazdy = Pojazd.query.order_by(Pojazd.marka.asc()).all()

    rows = ""
    for p in pojazdy:
        badanie, styl_bad = kolor_daty(p.badanie_techniczne)
        oc, styl_oc = kolor_daty(p.oc)
        tacho, styl_tacho = kolor_daty(p.tacho)

        rows += f"""
        <tr>
            <td>{p.nr_rejestracyjny}</td>
            <td>{p.vin}</td>
            <td>{p.marka} {p.model}</td>
            <td>{p.rok}</td>
            <td style="{styl_bad}">{badanie}</td>
            <td style="{styl_oc}">{oc}</td>
            <td style="{styl_tacho}">{tacho}</td>
            <td>
                <a class="btn btn-blue" href="/edytuj/{p.id}">Edytuj</a>
                <a class="btn btn-orange" href="/serwis/{p.id}">SERWIS</a>
                <a class="btn btn-red" href="/usun/{p.id}" onclick="return confirm('Na pewno usunąć pojazd?')">Usuń</a>
            </td>
        </tr>
        """

    return f"""
    {STYLE}
    <div class="header"><h1>System Floty – Paweł</h1></div>
    <div class="container">
        <a class="btn btn-green" href="/dodaj">+ Dodaj pojazd</a><br><br>
        <table>
            <tr>
                <th>Nr rej.</th>
                <th>VIN</th>
                <th>Marka/Model</th>
                <th>Rok</th>
                <th>Badanie</th>
                <th>OC</th>
                <th>Tacho</th>
                <th>Akcje</th>
            </tr>
            {rows}
        </table>
    </div>
    """

# ====== DODAJ POJAZD ======
@app.route("/dodaj", methods=["GET", "POST"])
def dodaj():
    if request.method == "POST":
        try:
            nowy = Pojazd(
                nr_rejestracyjny=request.form.get("nr"),
                vin=request.form.get("vin"),
                marka=request.form.get("marka"),
                model=request.form.get("model"),
                rok=int(request.form.get("rok")) if request.form.get("rok") else None,
                badanie_techniczne=request.form.get("badanie"),
                oc=request.form.get("oc"),
                tacho=request.form.get("tacho")
            )

            db.session.add(nowy)
            db.session.commit()

            return redirect("/")

        except Exception as e:
            db.session.rollback()
            return f"Błąd zapisu: {str(e)}"
    return f"""
    {STYLE}
    <div class="header"><h1>Dodaj pojazd</h1></div>
    <div class="container">
        <form method="post">
            Nr rejestracyjny:<br><input name="nr"><br>
            VIN:<br><input name="vin"><br>
            Marka:<br><input name="marka"><br>
            Model:<br><input name="model"><br>
            Rok:<br><input name="rok"><br>
            Badanie techniczne:<br><input type="date" name="badanie"><br>
            OC:<br><input type="date" name="oc"><br>
            Tacho:<br><input type="date" name="tacho"><br><br>
            <button>Zapisz</button>
        </form>
        <br>
        <a class="btn btn-blue" href="/">⬅ Powrót</a>
    </div>
    """
# ====== EDYTUJ POJAZD ======
@app.route("/edytuj/<int:id>", methods=["GET", "POST"])
def edytuj(id):
    pojazd = Pojazd.query.get_or_404(id)

    if request.method == "POST":
        try:
            pojazd.nr_rejestracyjny = request.form.get("nr")
            pojazd.vin = request.form.get("vin")
            pojazd.marka = request.form.get("marka")
            pojazd.model = request.form.get("model")
            pojazd.rok = int(request.form.get("rok")) if request.form.get("rok") else None
            pojazd.badanie_techniczne = request.form.get("badanie")
            pojazd.oc = request.form.get("oc")
            pojazd.tacho = request.form.get("tacho")

            db.session.commit()
            return redirect("/")

        except Exception as e:
            db.session.rollback()
            return f"Błąd edycji: {str(e)}"

    return f"""
    {STYLE}
    <div class="header"><h1>Edytuj pojazd</h1></div>
    <div class="container">
        <form method="post">
            Nr rejestracyjny:<br>
            <input name="nr" value="{pojazd.nr_rejestracyjny}"><br>

            VIN:<br>
            <input name="vin" value="{pojazd.vin}"><br>

            Marka:<br>
            <input name="marka" value="{pojazd.marka}"><br>

            Model:<br>
            <input name="model" value="{pojazd.model}"><br>

            Rok:<br>
            <input name="rok" value="{pojazd.rok if pojazd.rok else ''}"><br>

            Badanie techniczne:<br>
            <input type="date" name="badanie" value="{pojazd.badanie_techniczne or ''}"><br>

            OC:<br>
            <input type="date" name="oc" value="{pojazd.oc or ''}"><br>

            Tacho:<br>
            <input type="date" name="tacho" value="{pojazd.tacho or ''}"><br><br>

            <button>Zapisz zmiany</button>
        </form>
        <br>
        <a class="btn btn-blue" href="/">⬅ Powrót</a>
    </div>
    """

# ====== USUŃ POJAZD ======
@app.route("/usun/<int:id>")
def usun(id):
    pojazd = Pojazd.query.get(id)
    if pojazd:
        db.session.delete(pojazd)
        db.session.commit()
    return redirect("/")

# ====== SERWIS ======
@app.route("/serwis/<int:id>", methods=["GET", "POST"])
def serwis(id):
    pojazd = Pojazd.query.get_or_404(id)

    if request.method == "POST":
        try:
            nowy = Serwis(
                pojazd_id=id,
                data=request.form.get("data"),
                opis=request.form.get("opis"),
                przebieg=int(request.form.get("przebieg")) if request.form.get("przebieg") else None,
                koszt=float(request.form.get("koszt")) if request.form.get("koszt") else None
            )

            db.session.add(nowy)
            db.session.commit()

            return redirect(f"/serwis/{id}")

        except Exception as e:
            db.session.rollback()
            return f"Błąd serwisu: {str(e)}"

    wpisy = Serwis.query.filter_by(pojazd_id=id).order_by(Serwis.data.desc()).all()

    rows = ""
    for s in wpisy:
        rows += f"""
	<tr>
   	    <td>{s.data}</td>
            <td>{s.opis}</td>
            <td>{s.przebieg}</td>
            <td>{s.koszt}</td>
            <td>
        	<a class="btn btn-red"
           	   href="/usun_serwis/{s.id}"
           	   onclick="return confirm('Na pewno usunąć wpis serwisowy?')">
                   Usuń
        	</a>
    	    </td>
	</tr>
	"""

    return f"""
    {STYLE}
    <div class="header"><h1>Serwis – {pojazd.marka} {pojazd.model}</h1></div>
    <div class="container">

        <form method="post">
            Data:<br>
            <input type="date" name="data"><br>

            Opis:<br>
            <textarea name="opis"></textarea><br>

            Przebieg:<br>
            <input name="przebieg"><br>

            Koszt:<br>
            <input name="koszt"><br><br>

            <button>Dodaj wpis</button>
        </form>

        <br><br>

        <table>
            <tr>
                <th>Data</th>
                <th>Opis</th>
                <th>Przebieg</th>
                <th>Koszt</th>
		<th>Akcja</th>
            </tr>
            {rows}
        </table>

        <br>
        <a class="btn btn-blue" href="/">⬅ Powrót</a>
    </div>
    """
# ====== USUN Z SERWIS ======

@app.route("/usun_serwis/<int:id>")
def usun_serwis(id):
    wpis = Serwis.query.get_or_404(id)
    pojazd_id = wpis.pojazd_id

    try:
        db.session.delete(wpis)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Błąd usuwania: {str(e)}"

    return redirect(f"/serwis/{pojazd_id}")

# ====== START ======
if __name__ == "__main__":
    app.run()
=======
from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# ====== KONFIGURACJA BAZY ======
database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ====== MODELE ======
class Pojazd(db.Model):
    __tablename__ = "pojazdy"

    id = db.Column(db.Integer, primary_key=True)
    nr_rejestracyjny = db.Column(db.String(50))
    vin = db.Column(db.String(100))
    marka = db.Column(db.String(100))
    model = db.Column(db.String(100))
    rok = db.Column(db.Integer)
    badanie_techniczne = db.Column(db.String(20))
    oc = db.Column(db.String(20))
    tacho = db.Column(db.String(20))

    serwisy = db.relationship("Serwis", backref="pojazd", cascade="all, delete")

class Serwis(db.Model):
    __tablename__ = "serwis"

    id = db.Column(db.Integer, primary_key=True)
    pojazd_id = db.Column(db.Integer, db.ForeignKey("pojazdy.id"))
    data = db.Column(db.String(20))
    opis = db.Column(db.Text)
    przebieg = db.Column(db.Integer)
    koszt = db.Column(db.Float)

with app.app_context():
    db.create_all()

# ====== STYL ======
STYLE = """
<style>
body { font-family: Arial; background:#f4f6f9; margin:0; }
.btn-red { background-color: red; color: white; }
.header { background:#1f2937; color:white; padding:20px; }
.container { padding:30px; }
table { width:100%; border-collapse: collapse; background:white; }
th, td { padding:12px; border-bottom:1px solid #ddd; text-align:left; }
th { background:#111827; color:white; }
tr:hover { background:#f1f1f1; }
.btn { padding:6px 12px; text-decoration:none; border-radius:6px; font-size:14px; }
.btn-blue { background:#2563eb; color:white; }
.btn-green { background:#16a34a; color:white; }
.btn-orange { background:#ea580c; color:white; }
form input, form textarea { padding:8px; margin-bottom:10px; width:300px; }
form button { padding:10px 20px; background:#2563eb; color:white; border:none; border-radius:6px; }
</style>
"""

# ====== KOLOR DAT ======
def kolor_daty(data):
    if not data:
        return "-", ""

    try:
        dzis = datetime.today().date()
        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        roznica = (data_obj - dzis).days

        if roznica <= 9:
            return data, "background-color:#fecaca;"
        elif 10 <= roznica <= 30:
            return data, "background-color:#fef08a;"
        else:
            return data, ""
    except:
        return data, ""

# ====== STRONA GŁÓWNA ======
@app.route("/")
def index():
    pojazdy = Pojazd.query.order_by(Pojazd.marka.asc()).all()

    rows = ""
    for p in pojazdy:
        badanie, styl_bad = kolor_daty(p.badanie_techniczne)
        oc, styl_oc = kolor_daty(p.oc)
        tacho, styl_tacho = kolor_daty(p.tacho)

        rows += f"""
        <tr>
            <td>{p.nr_rejestracyjny}</td>
            <td>{p.vin}</td>
            <td>{p.marka} {p.model}</td>
            <td>{p.rok}</td>
            <td style="{styl_bad}">{badanie}</td>
            <td style="{styl_oc}">{oc}</td>
            <td style="{styl_tacho}">{tacho}</td>
            <td>
                <a class="btn btn-blue" href="/edytuj/{p.id}">Edytuj</a>
                <a class="btn btn-orange" href="/serwis/{p.id}">SERWIS</a>
                <a class="btn btn-red" href="/usun/{p.id}" onclick="return confirm('Na pewno usunąć pojazd?')">Usuń</a>
            </td>
        </tr>
        """

    return f"""
    {STYLE}
    <div class="header"><h1>System Floty – Paweł</h1></div>
    <div class="container">
        <a class="btn btn-green" href="/dodaj">+ Dodaj pojazd</a><br><br>
        <table>
            <tr>
                <th>Nr rej.</th>
                <th>VIN</th>
                <th>Marka/Model</th>
                <th>Rok</th>
                <th>Badanie</th>
                <th>OC</th>
                <th>Tacho</th>
                <th>Akcje</th>
            </tr>
            {rows}
        </table>
    </div>
    """

# ====== DODAJ POJAZD ======
@app.route("/dodaj", methods=["GET", "POST"])
def dodaj():
    if request.method == "POST":
        try:
            nowy = Pojazd(
                nr_rejestracyjny=request.form.get("nr"),
                vin=request.form.get("vin"),
                marka=request.form.get("marka"),
                model=request.form.get("model"),
                rok=int(request.form.get("rok")) if request.form.get("rok") else None,
                badanie_techniczne=request.form.get("badanie"),
                oc=request.form.get("oc"),
                tacho=request.form.get("tacho")
            )

            db.session.add(nowy)
            db.session.commit()

            return redirect("/")

        except Exception as e:
            db.session.rollback()
            return f"Błąd zapisu: {str(e)}"
    return f"""
    {STYLE}
    <div class="header"><h1>Dodaj pojazd</h1></div>
    <div class="container">
        <form method="post">
            Nr rejestracyjny:<br><input name="nr"><br>
            VIN:<br><input name="vin"><br>
            Marka:<br><input name="marka"><br>
            Model:<br><input name="model"><br>
            Rok:<br><input name="rok"><br>
            Badanie techniczne:<br><input type="date" name="badanie"><br>
            OC:<br><input type="date" name="oc"><br>
            Tacho:<br><input type="date" name="tacho"><br><br>
            <button>Zapisz</button>
        </form>
        <br>
        <a class="btn btn-blue" href="/">⬅ Powrót</a>
    </div>
    """
# ====== EDYTUJ POJAZD ======
@app.route("/edytuj/<int:id>", methods=["GET", "POST"])
def edytuj(id):
    pojazd = Pojazd.query.get_or_404(id)

    if request.method == "POST":
        try:
            pojazd.nr_rejestracyjny = request.form.get("nr")
            pojazd.vin = request.form.get("vin")
            pojazd.marka = request.form.get("marka")
            pojazd.model = request.form.get("model")
            pojazd.rok = int(request.form.get("rok")) if request.form.get("rok") else None
            pojazd.badanie_techniczne = request.form.get("badanie")
            pojazd.oc = request.form.get("oc")
            pojazd.tacho = request.form.get("tacho")

            db.session.commit()
            return redirect("/")

        except Exception as e:
            db.session.rollback()
            return f"Błąd edycji: {str(e)}"

    return f"""
    {STYLE}
    <div class="header"><h1>Edytuj pojazd</h1></div>
    <div class="container">
        <form method="post">
            Nr rejestracyjny:<br>
            <input name="nr" value="{pojazd.nr_rejestracyjny}"><br>

            VIN:<br>
            <input name="vin" value="{pojazd.vin}"><br>

            Marka:<br>
            <input name="marka" value="{pojazd.marka}"><br>

            Model:<br>
            <input name="model" value="{pojazd.model}"><br>

            Rok:<br>
            <input name="rok" value="{pojazd.rok if pojazd.rok else ''}"><br>

            Badanie techniczne:<br>
            <input type="date" name="badanie" value="{pojazd.badanie_techniczne or ''}"><br>

            OC:<br>
            <input type="date" name="oc" value="{pojazd.oc or ''}"><br>

            Tacho:<br>
            <input type="date" name="tacho" value="{pojazd.tacho or ''}"><br><br>

            <button>Zapisz zmiany</button>
        </form>
        <br>
        <a class="btn btn-blue" href="/">⬅ Powrót</a>
    </div>
    """

# ====== USUŃ POJAZD ======
@app.route("/usun/<int:id>")
def usun(id):
    pojazd = Pojazd.query.get(id)
    if pojazd:
        db.session.delete(pojazd)
        db.session.commit()
    return redirect("/")

# ====== SERWIS ======
@app.route("/serwis/<int:id>", methods=["GET", "POST"])
def serwis(id):
    pojazd = Pojazd.query.get_or_404(id)

    if request.method == "POST":
        try:
            nowy = Serwis(
                pojazd_id=id,
                data=request.form.get("data"),
                opis=request.form.get("opis"),
                przebieg=int(request.form.get("przebieg")) if request.form.get("przebieg") else None,
                koszt=float(request.form.get("koszt")) if request.form.get("koszt") else None
            )

            db.session.add(nowy)
            db.session.commit()

            return redirect(f"/serwis/{id}")

        except Exception as e:
            db.session.rollback()
            return f"Błąd serwisu: {str(e)}"

    wpisy = Serwis.query.filter_by(pojazd_id=id).order_by(Serwis.data.desc()).all()

    rows = ""
    for s in wpisy:
        rows += f"""
	<tr>
   	    <td>{s.data}</td>
            <td>{s.opis}</td>
            <td>{s.przebieg}</td>
            <td>{s.koszt}</td>
            <td>
        	<a class="btn btn-red"
           	   href="/usun_serwis/{s.id}"
           	   onclick="return confirm('Na pewno usunąć wpis serwisowy?')">
                   Usuń
        	</a>
    	    </td>
	</tr>
	"""

    return f"""
    {STYLE}
    <div class="header"><h1>Serwis – {pojazd.marka} {pojazd.model}</h1></div>
    <div class="container">

        <form method="post">
            Data:<br>
            <input type="date" name="data"><br>

            Opis:<br>
            <textarea name="opis"></textarea><br>

            Przebieg:<br>
            <input name="przebieg"><br>

            Koszt:<br>
            <input name="koszt"><br><br>

            <button>Dodaj wpis</button>
        </form>

        <br><br>

        <table>
            <tr>
                <th>Data</th>
                <th>Opis</th>
                <th>Przebieg</th>
                <th>Koszt</th>
		<th>Akcja</th>
            </tr>
            {rows}
        </table>

        <br>
        <a class="btn btn-blue" href="/">⬅ Powrót</a>
    </div>
    """
# ====== USUN Z SERWIS ======

@app.route("/usun_serwis/<int:id>")
def usun_serwis(id):
    wpis = Serwis.query.get_or_404(id)
    pojazd_id = wpis.pojazd_id

    try:
        db.session.delete(wpis)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Błąd usuwania: {str(e)}"

    return redirect(f"/serwis/{pojazd_id}")

# ====== START ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

