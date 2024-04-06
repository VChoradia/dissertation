from dotenv import load_dotenv
load_dotenv()

from app import app, create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=True)