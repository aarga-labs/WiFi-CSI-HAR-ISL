#!/usr/bin/env python3

from keras.layers import Dense, LSTM, Bidirectional, Embedding, Input, Concatenate
from keras.models import Sequential, Model


def get_LSTM(input_dim, output_dim, max_lenght, no_activities):
    model = Sequential(name='LSTM')
    model.add(Embedding(input_dim, output_dim, input_length=max_lenght, mask_zero=True))
    model.add(LSTM(output_dim, use_cudnn=False))
    model.add(Dense(no_activities, activation='softmax'))
    return model


def get_biLSTM(input_dim, output_dim, max_lenght, no_activities):
    model = Sequential(name='biLSTM')
    model.add(Embedding(input_dim, output_dim, input_length=max_lenght, mask_zero=True))
    model.add(Bidirectional(LSTM(output_dim, use_cudnn=False)))
    model.add(Dense(no_activities, activation='softmax'))
    return model


def get_Ensemble2LSTM(input_dim, output_dim, max_lenght, no_activities):
    # Two shared inputs; each branch gets the same sequence
    inp1 = Input(shape=(max_lenght,), name='input_1')
    inp2 = Input(shape=(max_lenght,), name='input_2')

    emb1 = Embedding(input_dim, output_dim, input_length=max_lenght, mask_zero=True)(inp1)
    bilstm_out = Bidirectional(LSTM(output_dim, use_cudnn=False))(emb1)

    emb2 = Embedding(input_dim, output_dim, input_length=max_lenght, mask_zero=True)(inp2)
    lstm_out = LSTM(output_dim, use_cudnn=False)(emb2)

    merged = Concatenate()([bilstm_out, lstm_out])
    output = Dense(no_activities, activation='softmax')(merged)

    model = Model(inputs=[inp1, inp2], outputs=output, name='Ensemble2LSTM')
    return model


def get_CascadeEnsembleLSTM(input_dim, output_dim, max_lenght, no_activities):
    inp1 = Input(shape=(max_lenght,), name='input_1')
    inp2 = Input(shape=(max_lenght,), name='input_2')

    emb1 = Embedding(input_dim, output_dim, input_length=max_lenght, mask_zero=True)(inp1)
    bilstm_out = Bidirectional(LSTM(output_dim, return_sequences=True, use_cudnn=False))(emb1)

    emb2 = Embedding(input_dim, output_dim, input_length=max_lenght, mask_zero=True)(inp2)
    lstm_out = LSTM(output_dim, return_sequences=True, use_cudnn=False)(emb2)

    merged = Concatenate()([bilstm_out, lstm_out])
    cascade = LSTM(output_dim, use_cudnn=False)(merged)
    output = Dense(no_activities, activation='softmax')(cascade)

    model = Model(inputs=[inp1, inp2], outputs=output, name='CascadeEnsembleLSTM')
    return model


def get_CascadeLSTM(input_dim, output_dim, max_lenght, no_activities):
    model = Sequential(name='CascadeLSTM')
    model.add(Embedding(input_dim, output_dim, input_length=max_lenght, mask_zero=True))
    model.add(Bidirectional(LSTM(output_dim, return_sequences=True, use_cudnn=False)))
    model.add(LSTM(output_dim, use_cudnn=False))
    model.add(Dense(no_activities, activation='softmax'))
    return model


def compileModel(model):
    model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    print(model.summary())
    return model
