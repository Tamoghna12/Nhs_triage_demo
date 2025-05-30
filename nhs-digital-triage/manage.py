import os
import sys
import click
from datetime import datetime, timezone, timedelta
import json

# Add the current directory to the path to import our app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app import Patient, ChatMessage, TriageAssessment, SystemLog

@click.group()
def cli():
    """NHS Digital Triage Management Utility."""
    pass

@cli.command()
@click.option('--env', default='development', help='Environment to use')
def init_db(env):
    """Initialize the database."""
    app = create_app(env)
    with app.app_context():
        click.echo('Creating database tables...')
        db.create_all()
        click.echo('✅ Database initialized successfully!')

@cli.command()
@click.option('--env', default='development', help='Environment to use')
@click.confirmation_option(prompt='Are you sure you want to drop all data?')
def reset_db(env):
    """Reset the database (WARNING: Deletes all data)."""
    app = create_app(env)
    with app.app_context():
        click.echo('Dropping all tables...')
        db.drop_all()
        click.echo('Creating new tables...')
        db.create_all()
        click.echo('✅ Database reset successfully!')

@cli.command()
@click.option('--env', default='development', help='Environment to use')
def create_sample_data(env):
    """Create sample data for testing."""
    app = create_app(env)
    with app.app_context():
        click.echo('Creating sample patients...')
        
        # Sample patients
        patients = [
            {
                'session_id': 'sample-session-1',
                'first_name': 'John',
                'last_name': 'Smith',
                'age': 45,
                'gender': 'male',
                'phone': '07123456789',
                'existing_conditions': ['Diabetes', 'High blood pressure'],
                'current_medications': ['Metformin', 'Lisinopril'],
                'allergies': ['Penicillin']
            },
            {
                'session_id': 'sample-session-2',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'age': 32,
                'gender': 'female',
                'phone': '07987654321',
                'existing_conditions': ['Asthma'],
                'current_medications': ['Salbutamol inhaler'],
                'allergies': []
            },
            {
                'session_id': 'sample-session-3',
                'first_name': 'Mohammed',
                'last_name': 'Ali',
                'age': 28,
                'gender': 'male',
                'phone': '07555123456',
                'existing_conditions': [],
                'current_medications': [],
                'allergies': ['Shellfish']
            }
        ]
        
        for patient_data in patients:
            patient = Patient(**patient_data)
            db.session.add(patient)
        
        db.session.commit()
        
        # Create sample assessments
        click.echo('Creating sample assessments...')
        
        assessments = [
            {
                'session_id': 'sample-session-1',
                'patient_id': 1,
                'symptom_category': 'pain',
                'primary_symptom': 'Chest pain',
                'severity': 8,
                'duration': 'few-hours',
                'urgency_level': 'Emergency',
                'ai_response': 'Based on your symptoms, this requires immediate medical attention.'
            },
            {
                'session_id': 'sample-session-2',
                'patient_id': 2,
                'symptom_category': 'respiratory',
                'primary_symptom': 'Shortness of breath',
                'severity': 6,
                'duration': 'today',
                'urgency_level': 'Urgent',
                'ai_response': 'Given your asthma history, you should seek urgent medical advice.'
            },
            {
                'session_id': 'sample-session-3',
                'patient_id': 3,
                'symptom_category': 'digestive',
                'primary_symptom': 'Nausea',
                'severity': 4,
                'duration': 'yesterday',
                'urgency_level': 'Self-care',
                'ai_response': 'These symptoms can likely be managed with self-care measures.'
            }
        ]
        
        for assessment_data in assessments:
            assessment = TriageAssessment(**assessment_data)
            db.session.add(assessment)
        
        db.session.commit()
        click.echo('✅ Sample data created successfully!')

@cli.command()
@click.option('--env', default='development', help='Environment to use')
@click.option('--days', default=30, help='Days of data to retain')
def cleanup_data(env, days):
    """Clean up old data."""
    app = create_app(env)
    with app.app_context():
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Clean up old chat messages
        old_messages = ChatMessage.query.filter(ChatMessage.created_at < cutoff_date)
        message_count = old_messages.count()
        old_messages.delete()
        
        # Clean up old system logs
        old_logs = SystemLog.query.filter(SystemLog.created_at < cutoff_date)
        log_count = old_logs.count()
        old_logs.delete()
        
        db.session.commit()
        
        click.echo(f'✅ Cleaned up {message_count} old chat messages')
        click.echo(f'✅ Cleaned up {log_count} old system logs')

@cli.command()
@click.option('--env', default='development', help='Environment to use')
def show_stats(env):
    """Show system statistics."""
    app = create_app(env)
    with app.app_context():
        total_patients = Patient.query.count()
        total_assessments = TriageAssessment.query.count()
        total_messages = ChatMessage.query.count()
        
        # Urgency breakdown
        emergency = TriageAssessment.query.filter_by(urgency_level='Emergency').count()
        urgent = TriageAssessment.query.filter_by(urgency_level='Urgent').count()
        standard = TriageAssessment.query.filter_by(urgency_level='Standard').count()
        selfcare = TriageAssessment.query.filter_by(urgency_level='Self-care').count()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_assessments = TriageAssessment.query.filter(
            TriageAssessment.created_at > yesterday
        ).count()
        
        click.echo('\n📊 NHS Digital Triage System Statistics')
        click.echo('=' * 50)
        click.echo(f'Total Patients: {total_patients}')
        click.echo(f'Total Assessments: {total_assessments}')
        click.echo(f'Total Chat Messages: {total_messages}')
        click.echo(f'Recent Assessments (24h): {recent_assessments}')
        click.echo('\n🚨 Urgency Level Breakdown:')
        click.echo(f'  Emergency: {emergency}')
        click.echo(f'  Urgent: {urgent}')
        click.echo(f'  Standard: {standard}')
        click.echo(f'  Self-care: {selfcare}')

@cli.command()
@click.option('--env', default='development', help='Environment to use')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'csv']))
@click.option('--output', help='Output file path')
def export_data(env, output_format, output):
    """Export system data."""
    app = create_app(env)
    with app.app_context():
        if output_format == 'json':
            data = {
                'patients': [p.to_dict() for p in Patient.query.all()],
                'assessments': [a.to_dict() for a in TriageAssessment.query.all()],
                'export_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if output:
                with open(output, 'w') as f:
                    json.dump(data, f, indent=2)
                click.echo(f'✅ Data exported to {output}')
            else:
                click.echo(json.dumps(data, indent=2))
        
        elif output_format == 'csv':
            import csv
            
            if not output:
                output = f'nhs_triage_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            with open(output, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Patient Name', 'Age', 'Gender', 'Primary Symptom', 
                    'Severity', 'Urgency Level', 'Assessment Date'
                ])
                
                for assessment in TriageAssessment.query.all():
                    writer.writerow([
                        f"{assessment.patient.first_name} {assessment.patient.last_name}",
                        assessment.patient.age,
                        assessment.patient.gender,
                        assessment.primary_symptom,
                        assessment.severity,
                        assessment.urgency_level,
                        assessment.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    ])
            
            click.echo(f'✅ Data exported to {output}')

@cli.command()
@click.option('--env', default='development', help='Environment to use')
def check_health(env):
    """Perform system health check."""
    app = create_app(env)
    with app.app_context():
        click.echo('🏥 NHS Digital Triage Health Check')
        click.echo('=' * 40)
        
        # Database connectivity
        try:
            db.session.execute('SELECT 1')
            click.echo('✅ Database: Connected')
        except Exception as e:
            click.echo(f'❌ Database: Error - {e}')
        
        # Ollama connectivity
        from app import check_ollama
        if check_ollama():
            click.echo('✅ Ollama AI: Available')
        else:
            click.echo('❌ Ollama AI: Unavailable')
        
        # Disk space check
        import shutil
        total, used, free = shutil.disk_usage('.')
        free_gb = free // (1024**3)
        if free_gb > 1:
            click.echo(f'✅ Disk Space: {free_gb}GB available')
        else:
            click.echo(f'⚠️ Disk Space: Only {free_gb}GB available')
        
        # Recent errors
        recent_errors = SystemLog.query.filter_by(level='ERROR').filter(
            SystemLog.created_at > datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()
        
        if recent_errors == 0:
            click.echo('✅ System Errors: None in last 24h')
        else:
            click.echo(f'⚠️ System Errors: {recent_errors} in last 24h')

if __name__ == '__main__':
    cli()
