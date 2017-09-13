# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, login_user, logout_user

from kojak_flask.extensions import login_manager
from kojak_flask.public.forms import LoginForm, EditorForm
from kojak_flask.user.forms import RegisterForm
from kojak_flask.user.models import User
from kojak_flask.utils import flash_errors
from kojak_flask.nlp_magic import extract_named_entities, linkify_entity, get_wiki_page, create_hyperlink, extract_summary,                                       extract_keywords

blueprint = Blueprint('public', __name__, static_folder='../static')

#debugging
import sys
import chromelogger as console
import logging
LOG_FILENAME = 'views.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route('/', methods=['GET', 'POST'])
def home():
    """Home page."""
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash('You are logged in.', 'success')
            redirect_url = request.args.get('next') or url_for('user.members')
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template('public/home.html', form=form)


@blueprint.route('/logout/')
@login_required
def logout():
    """Logout."""
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.home'))


@blueprint.route('/register/', methods=['GET', 'POST'])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(username=form.username.data, email=form.email.data, password=form.password.data, active=True)
        flash('Thank you for registering. You can now log in.', 'success')
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)
    return render_template('public/register.html', form=form)


@blueprint.route('/about/')
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template('public/about.html', form=form)


### Editor
@blueprint.route('/editor/', methods=['GET'])
def editor():
    """Editor page."""
    return render_template('public/editor.html')

@blueprint.route('/editor/textproc/', methods=['GET', 'POST'])
def editor_textproc():
    """Background process to return NLP results for content of Quill Editor."""
    try:
        text = request.args.get('content', 0, type=str)
        ents = [ [ent['text']+" "] for ent in extract_named_entities(text).values()]
        #ents = [linkify_entity(ent) for ent in extract_named_entities(text).values()]
        #logging.debug(linkified_named_ents)
        
        return jsonify(ents=ents)
    
    except Exception as e:
        logging.debug(e)
        
@blueprint.route('/editor/textproc/linkify', methods=['GET', 'POST'])
def linkify():
    """Gets links for entities"""
    try:
        ents = request.args.get('ents', 0, type=str)
        linkified_ents = []
        for ent in ents:
            ent_url = get_wiki_page(ent)['url']
            linkified_ents.append(create_hyperlink(ent_url, ent))
        return jsonify(linkified_ents=linkified_ents)
    
    except Exception as e:
        logging.debug(e)

@blueprint.route('/editor/textproc/summarize', methods=['GET', 'POST'])
def get_summary():
    """Returns gensim extractive summary"""
    try:
        text = request.args.get('content', 0, type=str)
        
        if len(text)<1000:
            summary = None
        else:
            summary = extract_summary(text)
        return jsonify(summary=summary)
    
    except Exception as e:
        logging.debug(e)