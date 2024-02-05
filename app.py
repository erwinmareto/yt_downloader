from flask import Flask, render_template, redirect, request, flash, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from pytube import YouTube, Playlist
from pytube.exceptions import VideoUnavailable, VideoPrivate, VideoRegionBlocked
from cs50 import SQL
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "cs50"

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

now = datetime.now()
db = SQL("sqlite:///users.db")


@app.route('/', methods=["GET", "POST"])
def download():
    if request.method == "POST":
        link = request.form.get("yt-link")
        yt = YouTube(str(link))
        quality = request.form.get("quality")
        if quality == "high":
            video = yt.streams.get_highest_resolution()
        elif quality == "low":
            resolution = yt.streams.get_lowest_resolution()
            video = resolution

        try:
            video.download(output_path=rf'C:\Users\{os.getlogin()}\Downloads')
            if session.get("user_id") is not None:
                db.execute("INSERT INTO history (title, channel, size, time, user_id) VALUES(?, ?, ?, ?, ?)", yt.title, yt.author, video.filesize_mb, now, session["user_id"])
            flash(f"Successfully downloaded '{yt.title}'!")
        except VideoUnavailable or VideoPrivate or VideoRegionBlocked:
            flash("video is not available")
        return redirect('/')
    return render_template("index.html")


@app.route("/mp3", methods=["GET", "POST"])
def mp3_download():
    if request.method == "POST":
        link = request.form.get("yt-link")
        yt = YouTube(str(link))
        video = yt.streams.filter(only_audio=True).first()
        try:
            out_file = video.download(output_path=rf'C:\Users\{os.getlogin()}\Downloads')
            base, ext = os.path.splitext(out_file)
            new_file = base + ' audio.mp3'
            os.rename(out_file, new_file)
            flash(f"Successfully downloaded '{yt.title}'")
            if session.get("user_id") is not None:
                db.execute("INSERT INTO history (title, channel, size, time, user_id) VALUES(?, ?, ?, ?, ?)",
                           f"{yt.title} (audio)", yt.author, video.filesize_mb, now, session["user_id"])
            return redirect('/mp3')
        except VideoUnavailable or VideoPrivate or VideoRegionBlocked:
            flash("video is not available")
            return redirect('/mp3')
    return render_template("mp3.html")


@app.route("/playlist", methods=["GET", "POST"])
def pl_download():
    if request.method == "POST":
        playlist_url = request.form.get("yt-link")
        quality = request.form.get("quality")
        p = Playlist(playlist_url)
        for url in p.video_urls:
            try:
                yt = YouTube(url)
            except VideoUnavailable:
                flash(f'A video in "{p.title}" is unavailable.')
            else:
                if quality == "high":
                    video = yt.streams.get_highest_resolution()
                    video.download(output_path=rf'C:\Users\{os.getlogin()}\Downloads')
                elif quality == "low":
                    video = yt.streams.get_lowest_resolution()
                    video.download(output_path=rf'C:\Users\{os.getlogin()}\Downloads')
                elif quality == "MP3":
                    video = yt.streams.filter(only_audio=True).first()
                    out_file = video.download(output_path=rf'C:\Users\{os.getlogin()}\Downloads')
                    base, ext = os.path.splitext(out_file)
                    new_file = base + '.mp3'
                    os.rename(out_file, new_file)
                if session.get("user_id") is not None:
                    db.execute("INSERT INTO history (title, channel, size, time, user_id) VALUES(?, ?, ?, ?, ?)",
                               f"{yt.title}", yt.author, video.filesize_mb, now, session["user_id"])
        flash(f"Successfully downloaded '{p.title}' playlist")

    return render_template('playlist.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        confirm = request.form.get("confirmation")
        used = db.execute("SELECT username FROM users")

        if not username or not password or not confirm:
            flash("Please fill the fields")
            return redirect("/register")
        elif password != confirm:
            flash("Passwords did not match!")
            return redirect("/register")

        # Check if username already exists
        for acc in used:
            for name in acc.values():
                if name == username:
                    flash("username has been taken")
                    return redirect("/register")

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))
        login()
        flash("Registered!")

        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Username cannot be empty")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Password cannot be empty")
            return redirect("/login")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username or password")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


@app.route("/history")
def history():
    downloads = db.execute("SELECT * FROM history WHERE user_id = ?", session["user_id"])
    return render_template("history.html", downloads=downloads)
