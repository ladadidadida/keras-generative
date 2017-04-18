import os
import sys
import math
import struct
import argparse

import numpy as np
import scipy.misc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import keras
from keras.models import Model, Sequential
from keras.layers import Input, Flatten, Dense, Activation, Reshape, Dropout
from keras.layers import Convolution2D, Deconvolution2D, LeakyReLU, BatchNormalization
from keras.layers import UpSampling2D, AveragePooling2D, GlobalAveragePooling2D
from keras import backend as K

seed_dims = 100
n_filters = 128

def Decoder():
    inputs = Input(shape=(seed_dims,))

    # Fully connected layer
    x = Dense(8 * 8 * n_filters)(inputs)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Reshape((8, 8, n_filters))(x)

    # Layer 1
    x = Deconvolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    x = Deconvolution2D(filters=n_filters, kernel_size=(3, 3), strides=(2, 2), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    # Layer 2
    x = Deconvolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    x = Deconvolution2D(filters=n_filters, kernel_size=(3, 3), strides=(2, 2), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    # Layer 3
    x = Deconvolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    x = Deconvolution2D(filters=n_filters, kernel_size=(3, 3), strides=(2, 2), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    # Layer 4
    x = Deconvolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    x = Deconvolution2D(filters=3, kernel_size=(3, 3), padding='same')(x)
    x = Activation('tanh')(x)

    model = Model(inputs, x)
    return model

def Encoder():
    inputs = Input(shape=(64, 64, 3))

    # Layer 1
    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), strides=(2, 2), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    # Layer 2
    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), strides=(2, 2), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    # Layer 3
    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), strides=(2, 2), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    # Layer 4
    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    x = Convolution2D(filters=n_filters, kernel_size=(3, 3), strides=(2, 2), padding='same')(inputs)
    x = BatchNormalization()(x)
    x = LeakyReLU(alpha=0.3)(x)

    # Fully connected layer
    x = Flatten()(x)
    x = Dense(seed_dims)(x)
    x = Activation('softmax')(x)

    model = Model(inputs, x)
    return model

def generator_loss(ae_in, ae_out):
    def lossfun(y_true, y_pred):
        ae_input = ae_in * 0.5 + 0.5
        ae_output = ae_out * 0.5 + 0.5

        size = K.shape(ae_input)[1:]
        scale = K.cast(K.prod(size), 'float32')

        return K.mean(keras.metrics.binary_crossentropy(ae_input, ae_output)) * scale

    return lossfun

def discriminator_loss(ae_in1, ae_in2, ae_out1, ae_out2):
    def lossfun(y_true, y_pred):
        ae_input1 = ae_in1 * 0.5 + 0.5
        ae_output1 = ae_out1 * 0.5 + 0.5
        ae_input2 = ae_in2 * 0.5 + 0.5
        ae_output2 = ae_out2 * 0.5 + 0.5

        size = K.shape(ae_input1)[1:]
        scale = K.cast(K.prod(size), 'float32')

        loss1 = K.mean(keras.metrics.binary_crossentropy(ae_input1, ae_output1)) * scale
        loss2 = K.mean(keras.metrics.binary_crossentropy(ae_input2, ae_output2)) * scale

        return loss2 - loss1

    return lossfun

def save_images(gen, samples, output, epoch, batch=-1):
    imgs = gen.predict(samples) * 0.5 + 0.5
    imgs = np.clip(imgs, 0.0, 1.0)

    fig = plt.figure(figsize=(8, 8))
    grid = gridspec.GridSpec(10, 10, wspace=0.1, hspace=0.1)
    for i in range(100):
        ax = plt.Subplot(fig, grid[i])
        ax.imshow(imgs[i, :, :, :], interpolation='none', vmin=0.0, vmax=1.0)
        ax.axis('off')
        fig.add_subplot(ax)

    outfile = os.path.join(output, 'epoch_{:04d}.png'.format(epoch + 1))
    if batch >= 0:
        outfile = os.path.join(output, 'epoch_{:04d}-{:d}.png'.format(epoch + 1, batch))

    fig.savefig(outfile, dpi=200)
    plt.close(fig)

def set_trainable(model, train):
    model.trainable = train
    for l in model.layers:
        l.trainable = train

def progress_bar(x, maxval, width=40):
    tick = int(x / maxval * width)
    tick = min(tick, width)

    if tick == width:
        return '=' * tick

    return '=' * tick + '>' + ' ' * (width - tick - 1)

def load_data(folder, num_images=60000):
    files = [f for f in os.listdir(folder) if not f.startswith('.')]
    files = [os.path.join(folder, f) for f in files if f.endswith('.jpg')]

    if len(files) >= num_images:
        files = files[:num_images]

    print('Loading images...')
    n_images = len(files)
    data = [None] * n_images
    for i, f in enumerate(files):
        data[i] = scipy.misc.imread(f, mode='RGB')
        ratio = 100.0 * (i + 1) / n_images
        print('[ {:6.2f} % ] [ {} ]'.format(ratio, progress_bar(i + 1, n_images)), end='\r', flush=True)

    print('')

    print(n_images, 'images loaded!')
    return np.stack(data, axis=0)

def main():
    parser = argparse.ArgumentParser(description='Keras DCGAN')
    parser.add_argument('--data', required=True)
    parser.add_argument('--numtrain', type=int, default=60000)
    parser.add_argument('--epoch', type=int, default=100)
    parser.add_argument('--batchsize', type=int, default=50)
    parser.add_argument('--output', default='output')
    parser.add_argument('--result', default='result')

    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.mkdir(args.output)

    if not os.path.exists(args.result):
        os.mkdir(args.result)

    x_train = load_data(args.data, args.numtrain)
    x_train = x_train.astype('float32') / 255.0
    x_train = x_train * 2.0 - 1.0

    gen = Decoder()
    enc = Encoder()
    dec = Decoder()

    gen_optim = keras.optimizers.Adam(lr=2.0e-4, beta_1=0.5)
    dis_optim = keras.optimizers.Adam(lr=2.0e-4, beta_1=0.5)

    # Input for generator
    set_trainable(enc, False)
    set_trainable(dec, False)

    h_random_input = Input(shape=(seed_dims,))
    x_random = gen(h_random_input)

    h_random = enc(x_random)
    y_random = dec(h_random)

    gen_trainer = Model(h_random_input, y_random)
    gen_trainer.compile(loss=generator_loss(x_random, y_random),
                        optimizer=gen_optim)

    gen_trainer.summary()

    # Input for discriminator
    set_trainable(gen, False)
    set_trainable(enc, True)
    set_trainable(dec, True)

    x_data = Input(shape=(64, 64, 3))
    h_data = enc(x_data)
    y_data = dec(h_data)

    dis_trainer = Model(inputs=[h_random_input, x_data], outputs=y_data)

    dis_trainer.summary()

    dis_trainer.compile(loss=discriminator_loss(x_random, x_data, y_random, y_data),
                        optimizer=dis_optim)

    dis_trainer.summary()


    # Training loop
    num_data = len(x_train)
    samples = np.random.uniform(-1.0, 1.0, size=(100, seed_dims)).astype(np.float32)
    for e in range(args.epoch):
        perm = np.random.permutation(num_data)
        gen_loss_sum = np.float32(0.0)
        dis_loss_sum = np.float32(0.0)

        num_batches = (num_data + args.batchsize - 1) // args.batchsize
        for b in range(num_batches):
            batch_start = b * args.batchsize
            batch_end = min(batch_start + args.batchsize, num_data)
            batch_size = batch_end - batch_start
            indx = perm[batch_start:batch_end]

            x_batch = x_train[indx, :, :, :]
            h_rand_batch = np.random.uniform(-1.0, 1.0, size=(batch_size, seed_dims)).astype(np.float32)

            dummy_output = np.zeros(x_batch.shape)
            gen_loss = gen_trainer.train_on_batch(h_rand_batch, dummy_output)
            dis_loss = dis_trainer.train_on_batch([h_rand_batch, x_batch], dummy_output)

            # Show info
            gen_loss_sum += gen_loss
            dis_loss_sum += dis_loss
            if e == 0 and b == 0:
                print(' {:10s} | {:8s} | {:8s} | {:8s} '.format(
                    'epoch', 'done', 'gen loss', 'dis loss'))

            ratio = min(100.0, 100.0 * batch_end / num_data)
            print(' epoch #{:3s} | {:6.2f} % | {:8.6f} | {:8.6f} '.format(
                '%d' % (e + 1), ratio,
                gen_loss_sum / (b + 1), dis_loss_sum / (b + 1)), end='\r')

            if (b + 1) % 200 == 0:
                save_images(gen, samples, args.output, e, batch_end)

        print('')

        # Save model
        if (e + 1) % 10 == 0:
            dis.save_weights(os.path.join(args.result, 'weights_discriminator_epoch_{:04d}.hdf5'.format(e + 1)))
            gen.save_weights(os.path.join(args.result, 'weights_generator_epoch_{:04d}.hdf5'.format(e + 1)))

        # Show current generated images
        save_images(gen, samples, args.output, e)

if __name__ == '__main__':
    main()