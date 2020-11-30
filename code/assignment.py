import tensorflow as tf
import numpy as np
from tensorflow.keras import Model
from preprocess import get_data

class Model(tf.keras.Model):
    def __init__(self, vocab_size):
        """
        The Model class predicts the sentiment of a tweet 
        :param vocab_size: The number of unique words in the data
        """

        super(Model, self).__init__()

        # TODO: initialize vocab_size, emnbedding_size
        self.vocab_size = vocab_size
        # self.window_size = 20 
        self.embedding_size = 300
        self.learning_rate = 0.01
        self.batch_size = 500 
        # number of output classes 
        self.num_classes = 5 
        # LSTM units 
        self.units = 150

        # TODO: initialize embeddings and forward pass weights (weights, biases)
        self.optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.learning_rate)

        self.embedding_matrix = tf.keras.layers.Embedding(self.vocab_size, self.embedding_size, mask_zero=True)
        self.lstm = tf.keras.layers.LSTM(self.units, return_sequences=True, return_state=True)
        self.dense = tf.keras.layers.Dense(self.num_classes) # check this 
        
        # might want to use Weights matrix and matmul 
        # self.W = tf.Variable(tf.random.truncated_normal([self.units, self.units], stddev=.1))
        # self.dense_2 = tf.keras.layers.Dense(vocab_size)
    
    def call(self, inputs, initial_state):
        """
        ...

        :param inputs: batch of tweets of shape (batch_size, tweet_size)
        :param initial_state: 2-d array of shape (batch_size, rnn_size) as a tensor
        :return: the batch element probabilities as a tensor, a final_state (Note 1: If you use an LSTM, the final_state will be the last two RNN outputs, 
        Note 2: We only need to use the initial state during generation)
        using LSTM and only the probabilites as a tensor and a final_state as a tensor when using GRU 
        """
        # get the embeddings of the inputs 
        embedding = self.embedding_matrix(inputs) # shape (batch_size, tweet_size, embedding_size)
        # apply the LSTM layer forward pass
        lstm_out, state_1, state_2 = self.lstm(embedding) # shape lstm_out (batch_size, tweet_size, units)
        # because we want to average all vectors to determine sentiment, we reduce_mean on the lstm output
        outputs = tf.reduce_mean(lstm_out, axis=1) # shape outputs (batch_size, units)
        # apply the dense layer to get logits ((X*W)+b)
        logits = self.dense(outputs)
        # activation function to obtain probabilities 
        probabilites = tf.convert_to_tensor(tf.nn.softmax(logits))

        return logits, probabilites, (state_1, state_2)
    
    def loss(self, logits, labels):
        """
        Calculates average cross entropy sequence to sequence loss of the prediction

        :param logits: a matrix of shape (batch_size, tweet_size, vocab_size) as a tensor
        :param labels: matrix of shape (batch_size, tweet_size) containing the labels
        :return: the loss of the model as a tensor of size 1
        """
        loss = tf.keras.losses.sparse_categorical_crossentropy(labels, logits)
        return tf.reduce_mean(loss)

    def accuracy(self, probs, labels):
        """
        Calculates the accuracy in testing a sequence of tweets through our model

        :param probs: probabilities matrix of shape (batch_size, tweet_size) ?
        :param labels: labels matrix of shape (batch_size, tweet_size)
        :return: accuracy of the prediction on the batch of tweets
        """
        # decoded_symbols = tf.argmax(input=prbs, axis=2)
		# accuracy = tf.reduce_mean(tf.boolean_mask(tf.cast(tf.equal(decoded_symbols, labels), dtype=tf.float32),mask))
		# return accuracy

        decoded_symbols = tf.argmax(input=probs, axis=1)
        print("probabilities: \n")
        print(probs)
        print("LABELS")
        print(labels)
        accuracy = tf.reduce_mean(tf.cast(tf.equal(decoded_symbols, labels), dtype=tf.float32))
        return accuracy

def train(model, train_inputs, train_labels):
    """
    Runs through one epoch - all training examples.

    :param model: the initilized model to use for forward and backward pass
    :param train_inputs: train inputs (all inputs for training) of shape (num_inputs, tweet_size)
    :param train_labels: train labels (all labels for training) of shape (num_labels, tweet_size)
    :return: None
    """
    i = 0
    num_batch = 1

    # suffle our train data
    rows, columns = tf.shape(train_inputs)
    indices = tf.random.shuffle(np.arange(rows))
    train_inputs = tf.gather(train_inputs, indices) 
    train_labels = tf.gather(train_labels, indices)

    # have to think about how our data is set up here: our tweet lengths are inconsistent.  
    while (i+model.batch_size - 1) < len(train_inputs):
        print("Training batch: " + str(num_batch))
        # batching inputs and labels 
        ibatch = train_inputs[i: i+model.batch_size] # ibatch shape: (batch_size, max_length=50)
        lbatch = train_labels[i: i+model.batch_size]  # shape (batch_size)   
        with tf.GradientTape() as tape:
            # forward pass, returning probabilities
            logits, probs, _ = model.call(ibatch, initial_state=None)
            # computing loss
            loss = model.loss(logits, lbatch)
        # updating gradients
        gradients = tape.gradient(loss, model.trainable_variables)
        model.optimizer.apply_gradients(zip(gradients, model.trainable_variables))
        # incrementing counter
        i += model.batch_size
        num_batch += 1
    return None   

def test(model, test_inputs, test_labels):
    """
    Runs through one epoch - all testing examples

    :param model: the trained model to use for prediction
    :param test_inputs: train inputs (all inputs for testing) of shape (num_inputs,)
    :param test_labels: train labels (all labels for testing) of shape (num_labels,)
    :returns: perplexity of the test set
    """
    total_loss = 0
    total_acc = 0
    num_batches = 0
    i = 0
    # have to think about how our data is set up here: our tweet lengths are inconsistent.  
    while (i+model.batch_size - 1) < len(test_inputs):
        print("Testing batch: " + str(num_batches + 1))
        # batching inputs and labels
        ibatch = test_inputs[i: i+model.batch_size]
        lbatch = test_labels[i: i+model.batch_size]
        # forward pass, returning probabilities
        logits, probs, _ = model.call(ibatch, initial_state=None)
        # computing loss 
        loss = model.loss(logits, lbatch)
        total_loss += loss
        # computing accuracy
        acc = model.accuracy(probs, lbatch)
        print("accuracy: " + str(acc))
        total_acc += acc
        #incrementing counters
        num_batches += 1
        i += model.batch_size
    # computing average accuracy and loss 
    avg_acc = total_acc/num_batches
    avg_loss = total_loss/num_batches
    return avg_acc, avg_loss

def main():
    # TO-DO: Pre-process and vectorize the data
    train_inputs, train_labels, test_inputs, test_labels, vocab_dict = get_data(
        '../data/train.csv', '../data/test.csv')
    # train_inputs, train_labels, test_inputs, test_labels, vocab_dict = get_data(
    #     '../data/train_mini.csv', '../data/test.csv')

    # TODO: initialize model and tensorflow variables
    model = Model(len(vocab_dict))

    # TODO: Set-up the training step
    train(model, train_inputs, train_labels)

    # TODO: Set up the testing steps
    accuracy, loss = test(model, test_inputs, test_labels)

    # print the ducking accuracy!! 
    print(accuracy)

if __name__ == '__main__':
    main()