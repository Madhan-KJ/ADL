from flask import Blueprint, render_template, request, url_for, redirect, flash
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../supabase')))
from supabase1.clients import supabase

common_routes = Blueprint('common_routes', __name__)

# Route to display Existing Titles page
@common_routes.route('/existing_titles', methods=['GET', 'POST'])
def existing_titles():
    # Pagination settings
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of titles per page
    offset = (page - 1) * per_page

    # Handle search, sort, and filter
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'title')  # Default sort is by title
    filter_by = request.args.get('filter', '')

    # Build query
    query = supabase.table('titles').select('*')

    # Apply search filter
    if search_query:
        query = query.ilike('title', f'%{search_query}%')

    # Apply language filter
    if filter_by:
        query = query.ilike('language', f'%{filter_by}%')

    # Apply sorting
    if sort_by == 'Title A-Z':
        query = query.order('title')
    elif sort_by == 'Title Z-A':
        query = query.order('title', desc=True)
    elif sort_by == 'Publisher A-Z':
        query = query.order('publisher')
    elif sort_by == 'Language':
        query = query.order('language')

    # Paginate the query
    titles = query.limit(per_page).offset(offset).execute()

    # Get total count for pagination
    total_titles = supabase.table('titles').select('id').execute()

    total_pages = len(total_titles.data) // per_page + (1 if len(total_titles.data) % per_page > 0 else 0)

    return render_template(
        'etitles.html',
        titles=titles.data,
        total_pages=total_pages,
        current_page=page,
        search_query=search_query,
        sort_by=sort_by,
        filter_by=filter_by
    )

@common_routes.route('/settings/<username>/')
def settings(username):
    user = supabase.table('users').select('*').eq('username', username).execute().data
    return render_template('Settings.html', current_user=username, user=user[0])

@common_routes.route('/update-settings', methods=['POST'])
def update_settings():
    # Handle form submission
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password and new_password != confirm_password:
        return "Passwords don't match", 400
        
    # Update user settings...
    name = request.form.get('name')
    username = request.form.get('username')
    email = request.form.get('email')
    notify = True if request.form.get('push_notifications')=='yes' else False

    supabase.table('users').update({'full_name':name, 'username':username, 'email': email, 'notification':notify}).eq('username',username).execute()
    if new_password:
        supabase.table('users').update({'password':new_password}).eq('username',username).execute()

    return redirect(url_for('common_routes.settings',username=username))

@common_routes.route('/delete-account', methods=['POST', 'get'])
def delete_account():
    # Delete account logic...
    username=request.args.get('username')
    supabase.table('users').delete().eq('username',username).execute()
    flash("Your account is permanently deleted!!!", 'success')
    return redirect(url_for('auth.hero'))

@common_routes.route('/support/<username>')
def support(username):
    return render_template('Support.html', username=username)

@common_routes.route('/submit-support-query/<username>', methods=['POST'])
def submit_query(username):
    query = request.form.get('query')
    role = supabase.table('users').select('role').eq('username', username).execute().data[0]['role']
    supabase.table('support_queries').insert({
        'username': username,
        'role': role,
        'query': query
    }).execute()
    flash('Support Query Sent...', 'success')
    return redirect(url_for('common_routes.support',username=username))

@common_routes.route('/help')
def helper():
    return render_template('help.html')