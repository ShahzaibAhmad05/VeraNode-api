import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = app.config.get('PORT', 3008)
    debug = app.config.get('DEBUG', True)
    app.run(host='0.0.0.0', port=port, debug=debug)
