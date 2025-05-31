from flask import Blueprint, render_template, request, redirect, url_for, flash
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../supabase')))
from supabase1.clients import supabase  # Import your Supabase client
from datetime import datetime

official_routes = Blueprint('official_routes', __name__)

# Route for the official dashboard
@official_routes.route('/official_dashboard/<username>')
def official_dashboard(username):
    # Fetch recently registered titles from the Supabase table
    registered_titles = supabase.table('titles').select('*').order('timestamp', desc=True).limit(10).execute().data

    # Render the dashboard page with the list of recently registered titles
    return render_template('dashboard2.html', registered_titles=registered_titles, username=username, enumerate=enumerate)

# Route for managing acceptance probability (for future implementation)
@official_routes.route('/acceptance_probability/<username>', methods=['POST', 'GET'])
def acceptance_probability(username):
    if request.method == 'POST':
        prob = request.form.get('prob')
        supabase.table('acceptance_probability').update({'prob':prob}).gt('prob',30).execute()
        return redirect(url_for('official_routes.acceptance_probability', username=username))
    proba = supabase.table('acceptance_probability').select('*').execute().data
    return render_template('Acceptance Probability.html', username=username, prob=proba[0]['prob'])

# Route for settings (for future implementation)
@official_routes.route('/settings/<username>')
def settings(username):
    # Placeholder route for settings management
    return render_template('settings.html', username=username)

# Route for managing restricted words and affixes
@official_routes.route('/restrictions/<username>')
def restrictions(username):
    # Fetch restricted words and affixes from Supabase
    restricted_words = supabase.table('restricted_words').select('*').execute().data
    restricted_affixes = supabase.table('restricted_affixes').select('*').execute().data
    
    # Render the restrictions page with the data
    return render_template('restriction.html', restricted_words=restricted_words, restricted_affixes=restricted_affixes, username=username, enumerate=enumerate)

@official_routes.route('/add_word/by_<username>', methods=['POST'])
def add_word(username):
    new_word=request.form.get('new_word')
    supabase.table('restricted_words').insert({
        'word': new_word,
        'updated_by': username
    }).execute()
    return redirect(url_for('official_routes.restrictions', username=username))

# Route to update a restricted word
@official_routes.route('/update_word/by_<username>', methods=['POST'])
def update_word(username):
    word_id = request.form.get('word_id')
    new_word = request.form.get('new_word')
    
    # Update the word in the Supabase table
    supabase.table('restricted_words').update({'word': new_word, 'updated_by': username}).eq('id', word_id).execute()

    return redirect(url_for('official_routes.restrictions', username=username))

# Route to delete a restricted word
@official_routes.route('/delete_word/by_<username>', methods=['POST'])
def delete_word(username):
    word_id = request.form.get('word_id')
    
    # Delete the word from the Supabase table
    supabase.table('restricted_words').delete().eq('id', word_id).execute()

    return redirect(url_for('official_routes.restrictions', username=username))

@official_routes.route('/add_affix/by_<username>', methods=['POST'])
def add_affix(username):
    new_affix = request.form.get('new_affix')
    affix_type = request.form.get('affix_type')
    supabase.table('restricted_affixes').insert({
        'affix': new_affix,
        'type': affix_type,
        'updated_by': username
    }).execute()
    return redirect(url_for('official_routes.restrictions', username=username))

# Route to update a restricted affix
@official_routes.route('/update_affix/by_<username>', methods=['POST'])
def update_affix(username):
    affix_id = request.form.get('affix_id')
    new_affix = request.form.get('new_affix')
    affix_type = request.form.get('affix_type')
    
    # Update the affix in the Supabase table
    supabase.table('restricted_affixes').update({'affix': new_affix, 'type': affix_type, 'updated_by': username}).eq('id', affix_id).execute()

    return redirect(url_for('official_routes.restrictions', username=username))

# Route to delete a restricted affix
@official_routes.route('/delete_affix/by_<username>', methods=['POST'])
def delete_affix(username):
    affix_id = request.form.get('affix_id')
    
    # Delete the affix from the Supabase table
    supabase.table('restricted_affixes').delete().eq('id', affix_id).execute()

    return redirect(url_for('official_routes.restrictions', username=username))