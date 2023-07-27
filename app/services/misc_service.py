from app import db, current_app
from app.models import User, Post
from flask_login import current_user
import os

def delete_stranded_posts():
    posts = Post.query.filter_by(user_id=None)
    for p in posts:
        print(p)
        db.session.delete(p)
        db.session.commit()

def delete_stranded_user_images():
    path = os.path.join(current_app.root_path, "static", "profile_pictures")
    users_with_images = User.query
    all_images = []
    used_images = []
    for f in os.listdir(path):
        all_images.append(f)
    for u in users_with_images:
        print("image currently in use: ", u.uploaded_picture)
        used_images.append(u.uploaded_picture)
    for i in all_images:
        if i not in used_images and i != ".DS_Store":
            print("deleting ", i)
            full_path = os.path.join(path, i)
            os.remove(full_path)