from app import db
from app.models import User
from hashlib import md5
from flask import current_app
import requests
import shutil
import os


def gravatars(id):
    print("in gravatars")
    new_filename = "user" + str(id) + ".png"
    new_path = os.path.join(
        current_app.root_path, "static", "profile_pictures", new_filename
    )
    digest = md5(str(id).lower().encode("utf-8")).hexdigest()
    url = "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(digest, 256)
    data = requests.get(url, stream=True)
    if data.status_code == 200:
        with open(new_path, "wb") as f:
            data.raw.decode_content = True
            shutil.copyfileobj(data.raw, f)
    print("gravatars finished, new_filename: ", new_filename)
    return new_filename


def update_db():
    users = User.query.filter_by(uploaded_picture=None)
    for user in users:
        filename = "user" + str(user.id) + ".png"
        print(filename)
        print(user)
        user.uploaded_picture = filename
    db.session.commit()


def create_image_if_no_image(user):
    if not os.path.isfile(os.path.join(current_app.root_path, "static", "profile_pictures", user.uploaded_picture)):
        filename = gravatars(user.id)
        user.uploaded_picture = filename
        db.session.commit()