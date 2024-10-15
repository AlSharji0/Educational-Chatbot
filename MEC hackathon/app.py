import openai
import tensorflow as tf
from tensorflow.keras import layers, models
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

openai.api_key = ""

def cnn_lstm_text_encoder(vocab_size, embedding_dim, max_length):
    input_text = layers.Input(shape=(max_length,))
    x = layers.Embedding(vocab_size, embedding_dim, input_length=max_length)(input_text)
    x = layers.LSTM(64, return_sequences=False)(x)
    latent_space = layers.Dense(32, activation='relu')(x)
    
    x = layers.RepeatVector(max_length)(latent_space)
    x = layers.LSTM(64, return_sequences=True)(x)
    decoded = layers.TimeDistributed(layers.Dense(vocab_size, activation='softmax'))(x)
    
    autoencoder = models.Model(input_text, decoded)
    autoencoder.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
    
    return autoencoder

def chatbot(query, autoencoder, tokenizer, m_length, user_wants_related):
    """Main chatbot logic for answering math questions and generating related questions."""
    
    #Answer the math question
    response_math_answer = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that solves math questions."},
            {"role": "user", "content": f"Answer the following math question: '{query}' "}
        ],
        max_tokens=300
    )
    
    print("OpenAI Response: ", response_math_answer)
    math_answer = response_math_answer['choices'][0]['message']['content']

    if not user_wants_related:
        return {
            "math_answer": math_answer,
            "follow_up": "Do you want similar questions?"
        }
    
    related_questions = []
    if user_wants_related:
        # Add variation using the autoencoderthen refine with GPT
        encoded_query = tokenizer.texts_to_sequences([query])
        encoded_query = tf.keras.preprocessing.sequence.pad_sequences(encoded_query, maxlen=m_length, padding='post')
        
        decoded_query = autoencoder.predict(encoded_query)
        decoded_query_text = tokenizer.sequences_to_texts(decoded_query.argmax(axis=-1))
        
        response_related_questions = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates related math questions."},
                {"role": "user", "content": f"Here is a generated similar question: '{decoded_query_text[0]}'. Could you refine it?"}
            ],
            max_tokens=100
        )

        related_questions = response_related_questions['choices'][0]['message']['content'].strip().split("\n")
    
    return {
        "math_answer": math_answer,
        "related_questions": related_questions
    }

# Initialize tokenizer and autoencoder
tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=10000)
max_length = 100
vocab_size = 10000
embedding_dim = 128

autoencoder = cnn_lstm_text_encoder(vocab_size, embedding_dim, max_length)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve_question', methods=['POST'])
def solve_question():
    data = request.json
    print(f"Received POST data: {data}")
    query = data['query']
    
    result = chatbot(query, autoencoder, tokenizer, max_length, user_wants_related=False)

    print(f"Chatbot result: {result}")

    return jsonify(result)

@app.route('/related_questions', methods=['POST'])
def related_questions():
    data = request.json
    query = data['query']

    result = chatbot(query, autoencoder, tokenizer, max_length, user_wants_related=True)

    print(f"Related questions result: {result}")

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
