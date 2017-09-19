# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, login_user, logout_user

from kojak_flask.extensions import login_manager
from kojak_flask.public.forms import LoginForm, EditorForm
from kojak_flask.user.forms import RegisterForm
from kojak_flask.user.models import User
from kojak_flask.utils import flash_errors
from kojak_flask.nlp_magic import extract_named_entities, linkify_entity, get_wiki_page, create_hyperlink, extract_summary, extract_keywords, get_semantic_key_terms, linter_suggestions, to_textacy_doc, get_readability_stats, get_dbpedia_result_text, get_completions

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
            
           #render_template('public/home.html', form=form)
    return render_template('public/editor.html')   


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




# MAIN ALL-PURPOSE INPUT / OUTPUT FUNCTION
@blueprint.route('/editor/textproc/', methods=['GET', 'POST'])
def editor_textproc():
    """Background process to return NLP results for content of Quill Editor."""
    try:
        text = request.args.get('content', 0, type=str)
        ents = [ ['"' + ent['text'] + '", '] for ent in extract_named_entities(text).values()]
        completions = ""#get_completions(text)
        other = ""
        return jsonify(ents=ents, completions=completions, other=other)
    
    except Exception as e:
        logging.debug(e)
        

# SAVE EDITOR CONTENTS
@blueprint.route('/editor/save_contents', methods=['GET', 'POST']) #need to make this work as POST only
def save_contents():
    """Saves content of Quill Editor to a text file called latest_save.txt."""
    try:
        doc_html = request.args.get('contents', 0, type=str)
        with open("latest_save.txt", "w+") as text_file:
            text_file.write(doc_html)
        return doc_html
    
    except Exception as e:
        logging.debug(e)
        return "Error while saving."
    
# LOAD EDITOR CONTENTS
@blueprint.route('/editor/load_contents', methods=['GET'])
def load_contents():
    """Loads content of Quill Editor from latest_save.txt."""
    try:
        with open("latest_save.txt", "r") as delta_text:
            saved_text = delta_text.read()
            if len(saved_text)>0:
                return saved_text
            else:
                return '{"ops":[]}'

    except Exception as e:
        logging.debug(e)
        return "Error while loading."
        

# ENDPOINT FOR LINKIFICATION
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
    return

# ENDPOINT TO GET SUMMARIZATION
@blueprint.route('/editor/textproc/summarize', methods=['GET', 'POST'])
def get_summary():
    """Returns gensim extractive summary and textacy readability stats"""
    try:
        text = request.args.get('content', 0, type=str)
        
        if len(text)<300:
            summary = None
            readability = None
        else:
            summary = extract_summary(text)
            doc = to_textacy_doc(text)
            readability = get_readability_stats(doc)
        return jsonify(summary=summary, readability=readability)
    
    except Exception as e:
        logging.debug(e)

        
# ENDPOINT TO GET KEY TERMS
@blueprint.route('/editor/textproc/get_keyterms', methods=['GET', 'POST'])
def get_keyterms():
    """"""
    try:
        text = request.args.get('content', 0, type=str)
        if len(text) < 10:
            return jsonify(keyterms='')
        
        #checkbox_format = "<input type='checkbox' class='keyterm' name={kw} value='{kw}'><label for='{kw}'> {kw} </label>"
        
        basic_format = "<span class='keyterm' name={kw}> {kw}, </span>"
        keyterms = [basic_format.format(kw=keyword[0]) for keyword in get_semantic_key_terms(text)]
        
        return jsonify(keyterms=keyterms)
    
    except Exception as e:
        logging.debug(e)
        return
    
# ENDPOINT TO GET PROSELINT SUGGESTIONS
@blueprint.route('/editor/textproc/lint_prose', methods=['GET', 'POST'])
def lint_prose():
    """Takes text contents of editor and returns proselint suggestions."""
    try:
        text = request.args.get('content', 0, type=str)
        proselint_suggestions = linter_suggestions(text)
        
        return jsonify(proselint_suggestions = proselint_suggestions)
    
    except Exception as e:
        logging.debug(e)
        
        
# ENDPOINT TO GET SUGGESTED TEXT COMPLETIONS
@blueprint.route('/editor/textproc/completions', methods=['GET', 'POST'])
def try_completions():
    """Takes text contents of editor and returns sentence suggestions."""
    try:
        text = request.args.get('content', 0, type=str)
        completions = get_completions(text)
        #knowledge_corpus = anything with text
        
        
        return jsonify(completions = completions)
    
    except Exception as e:
        logging.debug(e)