from flask import Flask, render_template, redirect, url_for, session, flash
from flask_session import Session
from authlib.integrations.flask_client import OAuth
import os
import time

app = Flask(__name__)
app.secret_key = os.urandom(24) 
app.config['SESSION_TYPE'] = 'filesystem' 
app.config['SESSION_COOKIE_SECURE'] = False 
app.config['SESSION_COOKIE_HTTPONLY'] = True  
Session(app)

oauth = OAuth(app)

github = oauth.register(
    name='github',
    client_id='Ov23lictdSGqVpqvBN97',
    client_secret='b8c375b9d88026344109c1b9331b17e24a0d5750',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    client_kwargs={'scope': 'read:user,user:email'}, 
        redirect_uri='http://54.242.232.220:5000/auth/callback'
)


@app.route('/login')
def login():
    return github.authorize_redirect(redirect_uri=None)

@app.route('/github/login')
def login_github():
    
    return github.authorize_redirect(redirect_uri=url_for('auth_callback', _external=True))

@app.route('/auth/callback')
def auth_callback():
    try:
        token = github.authorize_access_token(redirect_uri='http://54.242.232.220:5000/auth/callback')  # Fetch access token
        if not token:
            flash('Failed to obtain access token from GitHub.', 'error')
        return redirect(url_for('login'))

        session['token'] = token
        session['expires'] = time.time() + token.get('expires_in', 3600)  

     
        resp = github.get('https://api.github.com/user', token=token)
        if resp.status_code != 200:
            flash('Failed to retrieve user information from GitHub.', 'error')
            return redirect(url_for('login'))

        user_info = resp.json()
    
        email_resp = github.get('https://api.github.com/user/emails', token=token)
        if email_resp.status_code == 200:
            email_data = email_resp.json()
           
            primary_email = next((email['email'] for email in email_data if email['primary']), None)
            user_info['email'] = primary_email  

        if 'login' not in user_info:
            flash('User information does not contain login.', 'error')
            return redirect(url_for('login'))

        session['profile'] = user_info
        flash('Successfully logged in!', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        flash(f'Authentication failed: {str(e)}', 'error')
        return redirect(url_for('login'))
    



@app.route('/')
def home():
    if 'profile' in session:  
        return redirect(url_for('profiles'))  
    return redirect(url_for('login'))  

@app.route('/profiles')
def profiles():
    user_info = session.get('profiles')
    if user_info: 
         return render_template('hopeworks.html', username=user_info['login'], profile=user_info)
    flash('You must be logged in to view this page.', 'error')
    return redirect(url_for('login'))  


@app.route('/volunteers')
def volunteer():
    return render_template('volunteers.html')
    return redirect('/github/login')
@app.route('/donation')
def donation():
    return render_template('donation.html')




@app.route('/signout')
def signout():

    session.clear()

def token_refresh():
   
    refresh_token = session.get('refresh_token')

    if refresh_token:

        try:
            token_response = github.get('https://github.com/login/oauth/access_token', 
                                         params={'grant_type': 'refresh_token', 'refresh_token': refresh_token})
            new_token = token_response.json()
            session['token'] = new_token
            session['expires'] = time.time() + new_token.get('expires_in', 3600)  # Update expiry time
            return True
        except Exception as e:
            flash(f'Token refresh failed: {str(e)}', 'error')
            return False
    return False

def token_validate():
    token = session.get('token')
    expires= session.get('expires')
    if token and expires:
        if time.time() < expires:
            return True 
        else:
           
            return token_refresh()
    return False



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)