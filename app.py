from flask import Flask

app = Flask(__name__)

if __name__ == '__main__':
    app.run()

@app.route("/")
def index():
    return "Hello, World!"

