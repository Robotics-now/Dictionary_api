from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

df = pd.read_csv('dictionary.csv')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/api/<word>')
def about(word):
    word = word.lower()
    definition = df.loc[df['word'] == word]["definition"].squeeze()
    return {
        'definition': definition,
        'word': word
    }

if __name__ == '__main__':
    print(app.url_map)
    app.run(debug=True)
