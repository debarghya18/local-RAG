#!/usr/bin/env python
"""
Local development runner for IntelliDocs without Docker
"""
import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def setup_environment():
    """Setup environment variables for local development"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intellidocs.settings_local')
    os.environ.setdefault('DEBUG', 'True')
    os.environ.setdefault('SECRET_KEY', 'local-dev-secret-key-change-in-production')
    os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1')
    
    # Use SQLite for local development
    os.environ.setdefault('DATABASE_URL', 'sqlite:///db.sqlite3')
    
    # Disable Redis-dependent features for local development
    os.environ.setdefault('USE_REDIS', 'False')
    os.environ.setdefault('USE_CELERY', 'False')
    
    # Set embedding model
    os.environ.setdefault('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Core dependencies for local development
    dependencies = [
        'django==4.2.7',
        'djangorestframework==3.14.0',
        'django-cors-headers==4.3.1',
        'streamlit==1.28.2',
        'sentence-transformers==2.2.2',
        'PyPDF2==3.0.1',
        'python-docx==0.8.11',
        'numpy==1.24.3',
        'pandas==2.0.3',
        'plotly==5.17.0',
        'PyJWT==2.8.0',
        'python-decouple==3.8',
        'requests==2.31.0',
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")

def run_migrations():
    """Run Django migrations"""
    print("🗄️ Running migrations...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        print("✅ Migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")

def create_superuser():
    """Create superuser for admin access"""
    print("👤 Creating superuser...")
    try:
        # Check if superuser exists
        result = subprocess.run([
            sys.executable, 'manage.py', 'shell', '-c',
            'from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())'
        ], capture_output=True, text=True)
        
        if 'True' not in result.stdout:
            # Create superuser
            subprocess.run([
                sys.executable, 'manage.py', 'createsuperuser',
                '--noinput', '--username', 'admin', '--email', 'admin@example.com'
            ], check=True, env={**os.environ, 'DJANGO_SUPERUSER_PASSWORD': 'admin123'})
            print("✅ Superuser created (admin/admin123)")
        else:
            print("✅ Superuser already exists")
    except subprocess.CalledProcessError as e:
        print(f"❌ Superuser creation failed: {e}")

def run_django_server():
    """Run Django development server"""
    print("🚀 Starting Django server...")
    subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])

def run_streamlit_app():
    """Run Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    time.sleep(5)  # Wait for Django to start
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'frontend/app.py', 
                   '--server.address=0.0.0.0', '--server.port=8501'])

def main():
    """Main function to start the application"""
    print("🚀 Starting IntelliDocs Local Development Server")
    print("=" * 50)
    
    # Setup
    setup_environment()
    install_dependencies()
    run_migrations()
    create_superuser()
    
    print("\n🎯 Starting services...")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:8501")
    print("Admin: http://localhost:8000/admin")
    
    # Start Django server in a separate thread
    django_thread = threading.Thread(target=run_django_server)
    django_thread.daemon = True
    django_thread.start()
    
    # Start Streamlit app
    try:
        run_streamlit_app()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

if __name__ == '__main__':
    main()