# -*- coding: utf-8 -*
from __future__ import print_function
import numpy as np
import theano
import theano.tensor as T
import lasagne
import codecs
import json
import random

#Lasagne Seed for Reproducibility

lasagne.random.set_rng(np.random.RandomState(1))

def isNativeLetter(s, transliteration):
    
    ### Checks if a character is from a native languge
    
    for c in s:
        if c not in transliteration:
            return False
    return True

def valid(sequence, transliteration):
    
    ### Replaces all non given characters with '#'
    
    valids = [u'\u2000', u'\u2001',';',':','-',',',' ','\n','\t'] + \
             [chr(ord('0') + i) for i in range(10)] + list(set(''.join([''.join([s for s in transliteration[c]]) for c in transliteration])))
    
    ans = []
    non_valids = []
    
    for c in sequence:
        if c in valids:
            ans.append(c)
        else:
            ans.append('#')
            non_valids.append(c)
    return (ans,non_valids)

def  toTranslit(prevc,c,nextc,trans):    
    
    ### Translates one character to translit, given probabilistic mapping. 
    ### Previous and next characters are given for some armenian-specific parts
    
    if not isNativeLetter(c, trans):
        return c
        
    ### Armenian Specific Snippet
    
    if(c == u'ո'):
        if(isNativeLetter(prevc, trans)):
            return u'o'
        return u'vo'
    if(c == u'Ո'):
        if(isNativeLetter(prevc, trans)):
            return u'O'
        return u'Vo'

    ###
    
    x = random.random()
    s = 0
    eps = 1e-6
    for i in trans[c]:
        s += trans[c][i]
        if( s > x - eps):
            return i
    print (c,s,"error")


def make_vocabulary_files(data, language, transliteration):

    ### Makes jsons for future mapping of letters to indices and vice versa

    pointer = 0
    done = False
    s_l = 100000
    chars = set()
    trans_chars = set()
    data = ' \t' + u'\u2001'  + data # to get these symbols in vocab
    while not done:
        new_p = min(pointer + s_l ,len(data))
        raw_native = data[pointer : new_p]
        if new_p != len(data):
            pointer = new_p
            raw_native = ' ' + raw_native + ' '
        else:
            raw_native = ' ' + raw_native + ' '
            done = True
        native = []
        translit = []
        for ind in range(1,len(raw_native)-1):
            trans_char = toTranslit(raw_native[ind-1], raw_native[ind], raw_native[ind+1], transliteration)
            translit.append(trans_char[0])
            if len(trans_char) > 1:
                native.append(u'\u2000')
                translit.append(trans_char[1])
            native.append(raw_native[ind])
        translit = valid(translit, transliteration)[0]
        for i in range(len(native)):
            if translit[i] == '#':
                native[i] = '#'
        chars = chars.union(set(native))
        trans_chars = trans_chars.union(set(translit))
        print(str(100.0*pointer/len(data)) + "% done       ", end='\r')
        
    chars = list(chars)
    char_to_index = { chars[i] : i for i in range(len(chars)) }
    index_to_char = { i : chars[i] for i in range(len(chars)) }
    
    open('languages/' + language + '/char_to_index.json','w').write(json.dumps(char_to_index))
    open('languages/' + language + '/index_to_char.json','w').write(json.dumps(index_to_char))
    
    trans_chars = list(trans_chars)
    trans_to_index = { trans_chars[i] : i for i in range(len(trans_chars)) }
    index_to_trans = { i : trans_chars[i] for i in range(len(trans_chars)) }
    trans_vocab_size = len(trans_chars)
    
    open('languages/' + language + '/trans_to_index.json','w').write(json.dumps(trans_to_index))
    open('languages/' + language + '/index_to_trans.json','w').write(json.dumps(index_to_trans))

def load_vocabulary(language):
    
    ### Loads vocabulary mappings from specified json files

    char_to_index = json.loads(open('languages/' + language + '/char_to_index.json').read())
    char_to_index = { i : int(char_to_index[i]) for i in char_to_index}
    
    index_to_char = json.loads(open('languages/' + language + '/index_to_char.json').read())
    index_to_char = { int(i) : index_to_char[i] for i in index_to_char}
    vocab_size = len(char_to_index)
    
    
    trans_to_index = json.loads(open('languages/' + language + '/trans_to_index.json').read())
    trans_to_index = { i : int(trans_to_index[i]) for i in trans_to_index}
    
    index_to_trans = json.loads(open('languages/' + language + '/index_to_trans.json').read())
    index_to_trans = { int(i) : index_to_trans[i] for i in index_to_trans}
    trans_vocab_size = len(trans_to_index)
    return (char_to_index, index_to_char, vocab_size, trans_to_index, index_to_trans, trans_vocab_size)

def one_hot_matrix_to_sentence(data, index_to_character):

    ### Converts one sequence of one hot vectors to a string sentence

    if data.shape[0] == 1:
        data = data[0]
    sentence = ""
    for i in data:
        sentence += index_to_character[np.argmax(i)]
    return sentence

def load_language_data(language, is_train = True):
    
    TEST_DATA_PATH = 'languages/' + language + '/data/test.txt'
    VALIDATION_DATA_PATH = 'languages/' + language + '/data/val.txt'
    TRAIN_DATA_PATH = 'languages/' + language + '/data/train.txt'
    long_letters = json.loads(codecs.open('languages/' + language + '/long_letters.json','r',encoding='utf-8').read())
    long_letter_mapping = { long_letters[i] : unichr(ord(u'\u2002') + i) for i in range(len(long_letters)) }
    trans = json.loads(codecs.open('languages/' + language + '/transliteration.json','r',encoding='utf-8').read())
    tmp_trans = trans.copy()
    for c in tmp_trans:
        if c in long_letters:
            trans[long_letter_mapping[c]] = trans[c]
    del tmp_trans
    
    if is_train:
        train_text = codecs.open(TRAIN_DATA_PATH, encoding='utf-8').read()
        val_text = codecs.open(VALIDATION_DATA_PATH, encoding='utf-8').read()
        
        for letter in long_letter_mapping:
            train_text = train_text.replace(letter,long_letter_mapping[letter])
            val_text = val_text.replace(letter,long_letter_mapping[letter])
        
        return (train_text, val_text, trans)
    else:
        test_text = codecs.open(TEST_DATA_PATH, encoding='utf-8').read()
        for letter in long_letter_mapping:
            test_text = test_text.replace(letter,long_letter_mapping[letter])
        long_letter_reverse_mapping = { long_letter_mapping[i] : i for i in long_letter_mapping } 
        
        return (test_text, trans, long_letter_reverse_mapping)
        
def gen_data(p, seq_len, batch_size, data, transliteration, trans_to_index, char_to_index, is_train = True):
    
    ### Generates training examples from data, starting from given index
    ### and returns the index where it stopped
    ### also returns the number of sequences skipped (because of lack of native characters)
    ### and a boolean showing whether generation passed one iteration over data or not
        
    trans_vocab_size = len(trans_to_index)
    vocab_size = len(char_to_index)
    samples = []
    batch_seq_len = 0
    non_native_sequences = 0
    turned = False
    
    for i in range(batch_size):
        while True:
            new_p = min(p+seq_len,len(data))
            raw_native = data[p:new_p]
            if new_p != len(data):
                if max([raw_native.rfind(u' '),raw_native.rfind(u'\t'),raw_native.rfind(u'\n')]) > 0:
                    new_p = max([raw_native.rfind(u' '),raw_native.rfind(u'\t'),raw_native.rfind(u'\n')]) 
                    raw_native = ' ' + raw_native[:new_p] + ' '
                    p += new_p
                else:
                    p = new_p
                    raw_native = ' ' + raw_native + ' '
            else:
                raw_native = ' ' + raw_native + ' '
                p = 0
                turned = True
            native_letter_count = sum([1 for c in raw_native if isNativeLetter(c, transliteration)])
            if not is_train or native_letter_count * 3 > len(raw_native):
                break
            else:
                non_native_sequences += 1

        native = []
        translit = []
        for ind in range(1,len(raw_native)-1):
            trans_char = toTranslit(raw_native[ind-1], raw_native[ind], raw_native[ind+1], transliteration)
            translit.append(trans_char[0])
            trans_ind = 1
            while len(trans_char) > trans_ind:
                native.append(u'\u2000')
                translit.append(trans_char[trans_ind])
                trans_ind += 1
            native.append(raw_native[ind])
            
        (translit,non_valids) = valid(translit, transliteration)
        for ind in range(len(native)):
            if translit[ind] == '#':
                native[ind] = '#' 
        
        x = np.zeros((len(native), trans_vocab_size))
        y = np.zeros((len(native), vocab_size))
        for ind in range(len(native)):
            x[ind,trans_to_index[translit[ind]]] = 1
            y[ind,char_to_index[native[ind]]] = 1
        
        batch_seq_len = max(batch_seq_len, len(native))
        samples.append((x,y))
        
    x = np.zeros((batch_size, batch_seq_len, trans_vocab_size))
    y = np.zeros((batch_size, batch_seq_len, vocab_size))
    
    for i in range(batch_size):
        x[i, : len(samples[i][0]), :] = samples[i][0]
        y[i, : len(samples[i][1]), :] = samples[i][1]
        for j in range(len(samples[i][0]), batch_seq_len):
            x[i, j, trans_to_index[u'\u2001']] = 1
            y[i, j, char_to_index[u'\u2001']] = 1
    
    if is_train:
        return (x,y,p,turned,non_native_sequences)
    
    else:
        return (x,y,non_valids,p,turned)

def define_model(N_HIDDEN, depth, LEARNING_RATE = 0.01,  GRAD_CLIP = 100, trans_vocab_size=0, vocab_size=0, is_train = False):
    
    ### Defines lasagne model
    ### Returns output layer and theano functions for training and computing the cost
    
    l_input = lasagne.layers.InputLayer(shape=(None, None, trans_vocab_size))
    network = l_input
    symbolic_batch_size = lasagne.layers.get_output(network).shape[0]
    
    while depth > 0 :
        
        l_forward = lasagne.layers.LSTMLayer(
            network, N_HIDDEN, grad_clipping=GRAD_CLIP,
            backwards=False)
        
        l_backward = lasagne.layers.LSTMLayer(
            network, N_HIDDEN, grad_clipping=GRAD_CLIP,
            backwards=True)
        
        network = lasagne.layers.ConcatLayer(incomings=[l_forward,l_backward], axis = 2)
        network = lasagne.layers.ReshapeLayer(network, (-1, 2*N_HIDDEN))
        network = lasagne.layers.DenseLayer(network, num_units=N_HIDDEN, W = lasagne.init.Normal(), nonlinearity=lasagne.nonlinearities.tanh)
        network = lasagne.layers.ReshapeLayer(network, (symbolic_batch_size, -1, N_HIDDEN))
        
        depth -= 1
    
    network = lasagne.layers.ReshapeLayer(network, (-1, N_HIDDEN) )
    l_input_reshape = lasagne.layers.ReshapeLayer(l_input, (-1, trans_vocab_size))
    network = lasagne.layers.ConcatLayer(incomings=[network,l_input_reshape], axis = 1)
    
    l_out = lasagne.layers.DenseLayer(network, num_units=vocab_size, W = lasagne.init.Normal(), nonlinearity=lasagne.nonlinearities.softmax)

    target_values = T.dmatrix('target_output')
    
    network_output = lasagne.layers.get_output(l_out)

    cost = T.nnet.categorical_crossentropy(network_output,target_values).mean()

    all_params = lasagne.layers.get_all_params(l_out,trainable=True)

    
    print("Compiling Functions ...")
    
    if is_train:
        
        print("Computing Updates ...")
        updates = lasagne.updates.adagrad(cost, all_params, LEARNING_RATE)
        compute_cost = theano.function([l_input.input_var, target_values], cost, allow_input_downcast=True)
        train = theano.function([l_input.input_var, target_values], cost, updates=updates, allow_input_downcast=True)
        return(l_out,train, compute_cost)
    
    else:
        guess = theano.function([l_input.input_var],network_output,allow_input_downcast=True)
        return(l_out, guess)
