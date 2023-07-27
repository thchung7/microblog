from datetime import datetime
from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    g,
    jsonify,
    current_app,
    send_from_directory,
)
from flask_login import current_user, login_required, logout_user
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Message, Notification
from app.translate import translate
from app.main import bp

from app.services.misc_service import delete_stranded_posts, delete_stranded_user_images
from werkzeug.utils import secure_filename
import os


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    Post.reindex()
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ""
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_("Your post is now live!"))
        return redirect(url_for("main.index"))
    page = request.args.get("page", 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url = url_for("main.index", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("main.index", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "index.html",
        title=_("Home"),
        form=form,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/explore")
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url = url_for("main.explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("main.explore", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "index.html",
        title=_("Explore"),
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url = (
        url_for("main.user", username=user.username, page=posts.next_num)
        if posts.has_next
        else None
    )
    prev_url = (
        url_for("main.user", username=user.username, page=posts.prev_num)
        if posts.has_prev
        else None
    )
    form = EmptyForm()
    return render_template(
        "user.html",
        user=user,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
        form=form,
    )


@bp.route("/edit_profile/<username>", methods=["GET", "POST"])
@login_required
def edit_profile(username):
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        filename = secure_filename(form.profile_picture.data.filename)
        if filename:
            if current_user.uploaded_picture:
                print(current_user.uploaded_picture)
                filepath = os.path.join(
                    current_app.root_path,
                    "static",
                    "profile_pictures",
                    current_user.uploaded_picture,
                )
                os.remove(filepath)
            if "gravatar" in filename:  # change to if user chose default option
                filename = "user" + str(current_user.id) + ".png"
            else:
                filename = "user" + str(current_user.id) + "." + filename.split(".")[-1]
            profile_picture_url = os.path.join(
                current_app.root_path, "static", "profile_pictures", filename
            )
            form.profile_picture.data.save(profile_picture_url)
            current_user.uploaded_picture = filename
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_("Your changes have been saved."))
        return redirect(url_for("main.user", username=username))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title=_("Edit Profile"), form=form)


@bp.route("/profile_pictures/<path:filename>")
@login_required
def profile_pictures(filename):
    path = os.path.join(current_app.root_path, "static", "profile_pictures")
    return send_from_directory(path, filename)


@bp.route("/delete/<int:id>")
@login_required
def delete_user(id):
    form = EditProfileForm(current_user.username)
    if id == current_user.id:
        try:
            current_user.delete()
            flash("User deleted successfully.")
            logout_user()
            return redirect(url_for("auth.login"))
        except Exception as e:
            print(e, flush=True)
            flash("Something went wrong, try again.")
            return render_template("edit_profile.html", form=form)
    else:
        flash("Sorry, that user can't be deleted.")
        return render_template("main.index")


@bp.route("/user/<username>/followers")
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    followers = []
    for u in User.query:
        if user.followed_by(u):
            followers.append(u)
    print("followers: ", followers)
    next_url = (
        url_for("main.followers", page=posts.next_num) if posts.has_next else None
    )
    prev_url = (
        url_for("main.followers", page=posts.prev_num) if posts.has_prev else None
    )
    return render_template(
        "followers.html",
        title=_("Followers"),
        user=user,
        followers=followers,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/user/<username>/following")
@login_required
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    followings = []
    for u in User.query:
        if user.is_following(u):
            followings.append(u)
    print("followings: ", followings)
    next_url = (
        url_for("main.following", page=posts.next_num) if posts.has_next else None
    )
    prev_url = (
        url_for("main.following", page=posts.prev_num) if posts.has_prev else None
    )
    return render_template(
        "following.html",
        title=_("Followers"),
        user=user,
        followings=followings,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_("User %(username)s not found.", username=username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash(_("You cannot follow yourself!"))
            return redirect(url_for("main.user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_("You are now following %(username)s!", username=username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_("User %(username)s not found.", username=username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash(_("You cannot unfollow yourself!"))
            return redirect(url_for("main.user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_("You have unfollowed %(username)s.", username=username))
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/like/<int:post_id>/<action>")
@login_required
def like(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == "like":
        current_user.like_post(post)
        db.session.commit()
    if action == "unlike":
        current_user.unlike_post(post)
        db.session.commit()
    return redirect(request.referrer)  # contains URL the request came from


@bp.route("/delete_post/<int:user_id>/<int:post_id>")
@login_required
def delete_post(user_id, post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if user_id == post.user_id:
        try:
            post.delete_post()
            return redirect(request.referrer)
        except Exception as e:
            print(e, flush=True)
            flash("An error occurred, try again later.")
            return redirect(request.referrer)
    else:
        flash("You cannot delete somebody else's post!")
        return redirect(request.referrer)


@bp.route("/translate", methods=["POST"])
@login_required
def translate_text():
    return jsonify(
        {
            "text": translate(
                request.form["text"],
                request.form["source_language"],
                request.form["dest_language"],
            )
        }
    )


@bp.route("/search")
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for("main.explore"))
    page = request.args.get("page", 1, type=int)
    posts, total = Post.search(
        g.search_form.q.data, page, current_app.config["POSTS_PER_PAGE"]
    )
    next_url = (
        url_for("main.search", q=g.search_form.q.data, page=page + 1)
        if total > page * current_app.config["POSTS_PER_PAGE"]
        else None
    )
    prev_url = (
        url_for("main.search", q=g.search_form.q.data, page=page - 1)
        if page > 1
        else None
    )
    return render_template(
        "search.html",
        title=_("Search"),
        posts=posts,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/user/<username>/popup")
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template("user_popup.html", user=user, form=form)


# TODO: send_message route has to direct to the dm conversation page
@bp.route("/send_message/<username>", methods=["GET", "POST"])
@login_required
def send_message(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, username=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification("unread_message_count", user.new_messages())
        db.session.commit()
        flash(_("Your message has been sent."))
        return redirect(url_for("main.user", username=username))
    return render_template(
        "send_message.html", title=_("Send Message"), form=form, username=username
    )


@bp.route("/messages")
@login_required
# TODO: change to show conversations, not messages
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0)
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()
    ).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url = (
        url_for("main.messages", page=messages.next_num) if messages.has_next else None
    )
    prev_url = (
        url_for("main.messages", page=messages.prev_num) if messages.has_prev else None
    )
    return render_template(
        "messages.html", messages=messages.items, next_url=next_url, prev_url=prev_url
    )


@bp.route("/messages/<username>")
@login_required
def messages_with(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    messages = (
        current_user.messages_with(user)
        .order_by(Message.timestamp.desc())
        .paginate(
            page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
        )
    )
    # TODO: use scroll, not pagination
    # next_url = (
    #     url_for("main.messages_with", username=username, page=messages.next_num)
    #     if messages.has_next
    #     else None
    # )
    # prev_url = (
    #     url_for("main.messages_with", username=username, page=messages.prev_num)
    #     if messages.has_prev
    #     else None
    # )
    return render_template(
        "messages_with.html",
        messages=messages.items,
        # next_url=next_url,
        # prev_url=prev_url,
        username=username,
    )


@bp.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since
    ).order_by(Notification.timestamp.asc())
    return jsonify(
        [
            {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp}
            for n in notifications
        ]
    )
