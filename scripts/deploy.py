#!/usr/bin/env python
"""
Deployment script for IntelliDocs
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_requirements():
    """Check if required tools are available"""
    print("🔍 Checking requirements...")
    
    required_tools = ['docker', 'docker-compose', 'python', 'pip']
    
    for tool in required_tools:
        if not run_command(f"which {tool}", f"Checking {tool}"):
            print(f"❌ {tool} not found. Please install it first.")
            return False
    
    return True

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up environment...")
    
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            print("📄 Creating .env file from .env.example...")
            subprocess.run(['cp', str(env_example), str(env_file)])
        else:
            print("❌ .env.example not found. Please create environment configuration.")
            return False
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        return False
    
    # Download spaCy model
    if not run_command("python -m spacy download en_core_web_sm", "Downloading spaCy model"):
        return False
    
    return True

def run_migrations():
    """Run database migrations"""
    print("🗄️ Running database migrations...")
    
    # Wait for database to be ready
    print("⏳ Waiting for database...")
    time.sleep(10)
    
    if not run_command("python manage.py migrate", "Running migrations"):
        return False
    
    return True

def collect_static():
    """Collect static files"""
    print("📁 Collecting static files...")
    
    return run_command("python manage.py collectstatic --noinput", "Collecting static files")

def create_superuser():
    """Create superuser if needed"""
    print("👤 Creating superuser...")
    
    # Check if superuser already exists
    result = subprocess.run([
        'python', 'manage.py', 'shell', '-c',
        'from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())'
    ], capture_output=True, text=True)
    
    if 'True' in result.stdout:
        print("✅ Superuser already exists")
        return True
    
    # Create superuser
    return run_command(
        'python manage.py createsuperuser --noinput --username admin --email admin@example.com',
        "Creating superuser"
    )

def start_services():
    """Start all services using docker-compose"""
    print("🚀 Starting services...")
    
    # Build and start services
    if not run_command("docker-compose build", "Building Docker images"):
        return False
    
    if not run_command("docker-compose up -d", "Starting services"):
        return False
    
    # Wait for services to be ready
    print("⏳ Waiting for services to start...")
    time.sleep(30)
    
    # Check service health
    if not run_command("docker-compose ps", "Checking service status"):
        return False
    
    return True

def run_tests():
    """Run test suite"""
    print("🧪 Running tests...")
    
    return run_command("python manage.py test", "Running test suite")

def main():
    """Main deployment function"""
    print("🚀 Starting IntelliDocs deployment...")
    
    steps = [
        ("Check requirements", check_requirements),
        ("Setup environment", setup_environment),
        ("Install dependencies", install_dependencies),
        ("Start services", start_services),
        ("Run migrations", run_migrations),
        ("Collect static files", collect_static),
        ("Create superuser", create_superuser),
        ("Run tests", run_tests),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"📋 Step: {step_name}")
        print(f"{'='*50}")
        
        if not step_func():
            print(f"❌ Deployment failed at step: {step_name}")
            sys.exit(1)
    
    print("\n🎉 Deployment completed successfully!")
    print("\n📊 Service URLs:")
    print("  Backend API: http://localhost:8000")
    print("  Frontend: http://localhost:8501")
    print("  Admin: http://localhost:8000/admin")
    print("\n📚 Next steps:")
    print("  1. Visit the frontend at http://localhost:8501")
    print("  2. Create an account or login")
    print("  3. Upload your first document")
    print("  4. Start asking questions!")

if __name__ == '__main__':
    main()