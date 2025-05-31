from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../supabase')))
from supabase1.clients import supabase  # Assuming supabase client is already initialized
import jellyfish
import difflib

user_routes = Blueprint('user_routes', __name__)

# Function to calculate similarity score between two titles
def calculate_similarity(title1: str, title2: str) -> float:
    # Phonetic similarity
    phonetic_sim = jellyfish.metaphone(title1) == jellyfish.metaphone(title2)
    if phonetic_sim:
        return 100.0
    
    # Textual similarity using difflib
    seq = difflib.SequenceMatcher(None, title1, title2)
    return seq.ratio() * 100  # Return as percentage

# Function to check if the title violates any rules (restricted words, prefix/suffix, etc.)
def check_title_rules(title: str) -> bool:
    # Check restricted words
    restricted_words = supabase.table('restricted_words').select('word').execute().data
    title_words = title.lower().split()
    for word in restricted_words:
        if word in title_words:
            return False  # Title contains a restricted word
    
    # Check disallowed prefixes and suffixes
    disallowed_prefixes_suffixes = supabase.table('restricted_affixes').select('affix','type').execute().data
    for item in disallowed_prefixes_suffixes:
        if item['type'] == 'prefix':
            if title.lower().startswith(item['affix']):
                return False
        else:
            if title.lower().endswith(item['affix']):
                return False
          # Title contains disallowed prefix/suffix
    
    # No rules violated
    return True

# Function to calculate verification probability
def calculate_verification_probability(similarity_score: float, title_violates_rules: bool) -> float:
    if title_violates_rules:
        return 0.0  # Probability is 0 if any rule is violated
    return 100.0 - similarity_score  # Verification probability = 100 - similarity score

# Route for Title Applicant Dashboard
@user_routes.route('/title_applicant_dashboard/<username>/')
def title_applicant_dashboard(username):
    return render_template('dashboard1.html', user=username)
 
# Route for analyzing title
@user_routes.route('/analysis/<username>/', methods=['GET', 'POST'])
def analyze_title(username):
    # Retrieve the title submitted by the applicant
    title=request.form['title']
    
    # Retrieve all existing titles
    existing_titles = supabase.table('titles').select('title').execute().data
    
    similarity_scores = []
    
    # Calculate similarity for all existing titles
    for existing_title in existing_titles:
        score = calculate_similarity(title, existing_title['title'])
        similarity_scores.append({
            'title': existing_title['title'],
            'similarity': score
        })
    
    # Find the highest similarity
    max_similarity = max(similarity_scores, key=lambda x: x['similarity'])
    
    # Check if any title rules are violated
    title_violates_rules = not check_title_rules(title)
    
    # Calculate the verification probability
    verification_prob = calculate_verification_probability(max_similarity['similarity'], title_violates_rules)
    
    prob = supabase.table('acceptance_probability').select('*').execute().data

    # Determine final status and feedback if rejected
    status = "Accepted" if verification_prob >= prob[0]['prob'] else "Rejected"
    feedback = ""
    
    if status == "Rejected":
        if title_violates_rules:
            feedback="Your title contains restricted words or restricted affixes"
        else:
            feedback="Your title is too similar to the title -- "+ max_similarity['title']
    
    # Store verification result in history (Supabase)
    supabase.table('history').insert({  # Assuming user_id is available in the title data
        'title': title,
        'result': status,
        'date': datetime.now().date().isoformat(),  # Store the timestamp
        'time': datetime.now().strftime("%H:%M:%S"),
        'section': 'verification',
        'username': username
    }).execute()

    return render_template(
        'analysis.html',
        similarity_scores=sorted(similarity_scores, key= lambda x:x['similarity'], reverse=True),
        similarity_percentage=max_similarity['similarity'],
        verification_probability=verification_prob,
        status=status,
        feedback=feedback,
        enumerate=enumerate,
        username=username,
        round=round
    )

# Route for registering the title (if accepted)
@user_routes.route('/register_title/<username>/', methods=['GET', 'POST'])
def register_title(username):
    if request.method == 'POST':
        title_data = request.form.to_dict()  # Get form data
        title = title_data['title-name']
        # Insert into the main titles table (Supabase)
        supabase.table('titles').insert({
            'title': title,
            'language': title_data['language'],
            'periodicity': title_data['periodicity'],
            'place': title_data['place'],
            'category': title_data['category'],
            'format': title_data['format'],
            'justification': title_data['justification'],
            'owner': title_data['owner-name'],
            'publisher': title_data['publisher-name'],
            'legal_entity': title_data['legal-entity'],
            'applicant_name': title_data['applicant-name'],
            'applicant_username': title_data['applicant-username'],
            'applicant_email': title_data['applicant-email'],
            'timestamp': datetime.now().isoformat()
        }).execute()

        # Record the registration in the history (Supabase)
        supabase.table('history').insert({  # Assuming user_id is available in the form data
            'title': title,
            'result': 'registered',  # Successful registration
            'date': datetime.now().date().isoformat(),  # Store the timestamp
            'time': datetime.now().strftime("%H:%M:%S"),
            'section': 'registration',
            'username': username 
        }).execute()

        return redirect(url_for('user_routes.title_applicant_dashboard', username=username))

    return render_template('registration.html', username=username)

# Route to view user history (Verification and Registration)
@user_routes.route('/history/<username>/')
def user_history(username):
    # Fetch verification history (from Supabase)
    
    verification_history = supabase.table('history').select('*').eq('section','verification').eq('username', username).execute().data
    
    # Fetch registration history (from Supabase)
    registration_history = supabase.table('history').select('*').eq('section', 'registration').eq('username', username).execute().data
    
    return render_template('history.html', 
                           verification_history=verification_history, 
                           registration_history=registration_history,
                           enumerate=enumerate)

@user_routes.route('/settings/')
def settings():
    return render_template('Settings.html')