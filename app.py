"""
SoundPulse Root Application Entrypoint
Exports Flask `app` for Render / WSGI servers default `gunicorn app:app`
"""
from dashboard.app import app

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)
