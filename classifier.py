from __future__ import print_function, division
import nltk
import os
import random
from collections import Counter
from nltk import word_tokenize, WordNetLemmatizer
from nltk.corpus import stopwords
from nltk import NaiveBayesClassifier, classify

from settings import BASEDIR


class Classifier:
    stoplist = stopwords.words('english')

    def __init__(self):
        self.classifier = self._train(self._get_training_set(), 0.8)

    @staticmethod
    def _get_training_list(folder):
        training_list = []
        file_list = os.listdir(folder)
        for email in file_list:
            f = open(folder + email, 'r')
            training_list.append(f.read())
        f.close()
        return training_list

    @staticmethod
    def _preprocess(sentence):
        lemmatizer = WordNetLemmatizer()
        return [lemmatizer.lemmatize(word.lower()) for word in word_tokenize(unicode(sentence, errors='ignore'))]

    def _get_features(self, text, setting):
        if setting == 'bow':
            return {word: count for word, count in Counter(self._preprocess(text)).items() if not word in stoplist}
        else:
            return {word: True for word in self._preprocess(text) if not word in self.stoplist}

    def _get_training_set(self):
        spam = self._get_training_list(BASEDIR + '/enron1/spam/')
        ham = self._get_training_list(BASEDIR + '/enron1/ham/')
        all_emails = [(email, 'spam/') for email in spam]
        all_emails += [(email, 'ham/') for email in ham]
        random.shuffle(all_emails)
        return [(self._get_features(email, ''), label) for (email, label) in all_emails]

    @staticmethod
    def _train(features, samples_proportion):
        train_size = int(len(features) * samples_proportion)
        train_set, test_set = features[:train_size], features[train_size:]
        classifier = NaiveBayesClassifier.train(train_set)
        return classifier

    def evaluate(train_set, test_set, classifier):
        print('Accuracy on the training set = ' + str(classify.accuracy(classifier, train_set)))
        print('Accuracy of the test set = ' + str(classify.accuracy(classifier, test_set)))
        classifier.show_most_informative_features(20)

    @staticmethod
    def _get_message_text(message):
        maintype = message.get_content_maintype()
        if maintype == 'multipart':
            for part in message.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        elif maintype == 'text':
            return message.get_payload()

    def classify(self, message):
        body = self._get_message_text(message)
        result = "ham"
        if body:
            result = self.classifier.classify(self._get_features(body, ""))
        return result
