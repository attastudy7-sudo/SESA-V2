from app import create_app, db
from waitress import serve

app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True, threaded=True)
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080)
