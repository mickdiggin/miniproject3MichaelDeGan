from flask import Flask

app = Flask(__name__) #in this case app __name__ is hello since the file name is hello


@app.route('/') #The part of the url that accesses the app
def hello(): #hello also happens to be the name of this page.
    return 'Hello, World!'