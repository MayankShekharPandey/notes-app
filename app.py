import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-12345")

# Initialize Supabase client directly
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
service_key = os.environ.get("SUPABASE_SERVICE_KEY")

if not all([url, key, service_key]):
    raise ValueError("Missing Supabase credentials in .env file")

supabase = create_client(url, key)
service_supabase = create_client(url, service_key)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    return session.get('user')

def get_safe_data(response):
    """Safely extract data from Supabase response"""
    if hasattr(response, 'data'):
        return response.data
    elif isinstance(response, dict) and 'data' in response:
        return response['data']
    else:
        return []

def get_safe_count(response):
    """Safely extract count from Supabase response"""
    if hasattr(response, 'count'):
        return response.count
    elif isinstance(response, dict) and 'count' in response:
        return response['count']
    else:
        return 0

# Routes
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                session['user'] = {
                    'id': response.user.id,
                    'email': response.user.email,
                    'access_token': response.session.access_token
                }
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        try:
            # Use service role to create user (bypasses email confirmation)
            response = service_supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"full_name": full_name}
            })
            
            if response.user:
                user_id = response.user.id
                
                # Create profile
                service_supabase.table('profiles').insert({
                    'id': user_id,
                    'email': email,
                    'full_name': full_name
                }).execute()
                
                # Create default categories
                default_categories = [
                    {'name': 'Personal', 'color': '#3498db', 'user_id': user_id},
                    {'name': 'Work', 'color': '#e74c3c', 'user_id': user_id},
                    {'name': 'Ideas', 'color': '#9b59b6', 'user_id': user_id},
                    {'name': 'Important', 'color': '#f39c12', 'user_id': user_id}
                ]
                
                for category in default_categories:
                    service_supabase.table('categories').insert(category).execute()
                
                flash('Registration successful! You can now login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed.', 'error')
                
        except Exception as e:
            error_msg = str(e)
            if 'already registered' in error_msg.lower():
                flash('Email already registered. Please login.', 'error')
            else:
                flash(f'Registration failed: {error_msg}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    
    # Get recent notes
    recent_notes_response = supabase.table('notes').select('*, categories(name, color)').eq('user_id', user['id']).order('created_at', desc=True).limit(5).execute()
    recent_notes = get_safe_data(recent_notes_response)
    
    # Get categories
    categories_response = supabase.table('categories').select('*').eq('user_id', user['id']).execute()
    categories = get_safe_data(categories_response)
    
    # Get counts
    total_notes_response = supabase.table('notes').select('*', count='exact').eq('user_id', user['id']).execute()
    important_notes_response = supabase.table('notes').select('*', count='exact').eq('user_id', user['id']).eq('is_important', True).execute()
    
    total_notes = get_safe_count(total_notes_response)
    important_notes_count = get_safe_count(important_notes_response)
    
    return render_template('index.html', 
                         recent_notes=recent_notes,
                         categories=categories,
                         total_notes=total_notes,
                         important_notes_count=important_notes_count)

@app.route('/all-notes')
@login_required
def all_notes():
    user = get_current_user()
    
    category_filter = request.args.get('category', 'all')
    
    if category_filter == 'all':
        notes_response = supabase.table('notes').select('*, categories(name, color)').eq('user_id', user['id']).order('created_at', desc=True).execute()
    else:
        notes_response = supabase.table('notes').select('*, categories(name, color)').eq('user_id', user['id']).eq('categories.name', category_filter).order('created_at', desc=True).execute()
    
    categories_response = supabase.table('categories').select('*').eq('user_id', user['id']).execute()
    
    notes = get_safe_data(notes_response)
    categories = get_safe_data(categories_response)
    
    return render_template('all_notes.html', 
                         notes=notes,
                         categories=categories,
                         current_category=category_filter)

@app.route('/important-notes')
@login_required
def important_notes():
    user = get_current_user()
    
    notes_response = supabase.table('notes').select('*, categories(name, color)').eq('user_id', user['id']).eq('is_important', True).order('created_at', desc=True).execute()
    notes = get_safe_data(notes_response)
    
    return render_template('important_notes.html', 
                         notes=notes)

@app.route('/add-note', methods=['GET', 'POST'])
@login_required
def add_note():
    user = get_current_user()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form.get('category_id') or None
        is_important = 'is_important' in request.form
        
        if title and content:
            try:
                note_data = {
                    'title': title,
                    'content': content,
                    'user_id': user['id'],
                    'is_important': is_important
                }
                
                if category_id:
                    note_data['category_id'] = category_id
                
                # Use service role to ensure insert works
                response = service_supabase.table('notes').insert(note_data).execute()
                response_data = get_safe_data(response)
                
                if response_data:
                    flash('Note added successfully!', 'success')
                    return redirect(url_for('all_notes'))
                else:
                    flash('Failed to add note. No data returned.', 'error')
                    
            except Exception as e:
                flash(f'Error adding note: {str(e)}', 'error')
        else:
            flash('Title and content are required!', 'error')
    
    try:
        categories_response = supabase.table('categories').select('*').eq('user_id', user['id']).execute()
        categories = get_safe_data(categories_response)
        return render_template('add_note.html', categories=categories)
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return render_template('add_note.html', categories=[])

@app.route('/toggle-important/<note_id>')
@login_required
def toggle_important(note_id):
    user = get_current_user()
    
    # Get current status
    note_response = supabase.table('notes').select('is_important').eq('id', note_id).eq('user_id', user['id']).execute()
    note_data = get_safe_data(note_response)
    
    if note_data:
        current_status = note_data[0]['is_important']
        supabase.table('notes').update({'is_important': not current_status}).eq('id', note_id).eq('user_id', user['id']).execute()
        flash('Note updated!', 'success')
    
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/delete-note/<note_id>')
@login_required
def delete_note(note_id):
    user = get_current_user()
    
    supabase.table('notes').delete().eq('id', note_id).eq('user_id', user['id']).execute()
    flash('Note deleted!', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/search')
@login_required
def search_notes():
    user = get_current_user()
    
    query = request.args.get('q', '')
    
    if query:
        notes_response = supabase.table('notes').select('*, categories(name, color)').eq('user_id', user['id']).ilike('title', f'%{query}%').order('created_at', desc=True).execute()
        notes = get_safe_data(notes_response)
    else:
        notes = []
    
    categories_response = supabase.table('categories').select('*').eq('user_id', user['id']).execute()
    categories = get_safe_data(categories_response)
    
    return render_template('search.html', 
                         notes=notes,
                         categories=categories,
                         search_query=query)

@app.route('/categories')
@login_required
def categories():
    user = get_current_user()
    
    categories_response = service_supabase.table('categories').select('*, notes(count)').eq('user_id', user['id']).execute()
    categories_data = get_safe_data(categories_response)
    
    return render_template('categories.html', 
                         categories=categories_data)

@app.route('/add-category', methods=['POST'])
@login_required
def add_category():
    user = get_current_user()
    
    category_name = request.form['category_name']
    category_color = request.form['category_color']
    
    if category_name:
        service_supabase.table('categories').insert({
            'name': category_name,
            'color': category_color,
            'user_id': user['id']
        }).execute()
        flash('Category added!', 'success')
    
    return redirect(url_for('categories'))

@app.route('/delete-category/<category_id>')
@login_required
def delete_category(category_id):
    user = get_current_user()
    
    # Remove category from notes first
    service_supabase.table('notes').update({'category_id': None}).eq('category_id', category_id).eq('user_id', user['id']).execute()
    # Delete category
    service_supabase.table('categories').delete().eq('id', category_id).eq('user_id', user['id']).execute()
    flash('Category deleted!', 'success')
    return redirect(url_for('categories'))

# Debug routes
@app.route('/debug-tables')
def debug_tables():
    """Check if tables are accessible"""
    try:
        profiles_response = service_supabase.table('profiles').select('*', count='exact').limit(5).execute()
        categories_response = service_supabase.table('categories').select('*', count='exact').limit(5).execute()
        notes_response = service_supabase.table('notes').select('*', count='exact').limit(5).execute()
        
        profiles = get_safe_data(profiles_response)
        categories = get_safe_data(categories_response)
        notes = get_safe_data(notes_response)
        
        return {
            'profiles': len(profiles),
            'categories': len(categories),
            'notes': len(notes),
            'sample_data': {
                'profiles': profiles[:2],
                'categories': categories[:2],
                'notes': notes[:2]
            }
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/test-insert')
@login_required
def test_insert():
    """Test inserting a note"""
    user = get_current_user()
    
    try:
        test_note = {
            'title': 'Test Note',
            'content': 'This is a test note',
            'user_id': user['id'],
            'is_important': False
        }
        
        response = service_supabase.table('notes').insert(test_note).execute()
        response_data = get_safe_data(response)
        
        if response_data:
            return {'success': True, 'note_id': response_data[0]['id']}
        else:
            return {'success': False, 'error': 'No data returned'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # Check if running on Vercel
    if os.environ.get('VERCEL'):
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        # Local development
        app.run(debug=True, host='localhost', port=5000)