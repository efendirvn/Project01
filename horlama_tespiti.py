# -*- coding: utf-8 -*-
"""Horlama Tespiti

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KkCGYexv5A3ZLRa33GYioNA5pTk3qvB6
"""

!pip install librosa matplotlib scikit-learn tensorflow keras sounddevice

# Install required libraries (if not already installed)

import os
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import pickle
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

# For reproducibility
np.random.seed(42)
tf.random.set_seed(42)



def load_audio(file_path, duration=5.0, sr=None):
    """Loads an audio file for the given duration."""
    try:
        y, sr = librosa.load(file_path, sr=sr, duration=duration)
        print(f"Loaded {file_path} at {sr}Hz")
        return y, sr
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None, None

def extract_mfcc(y, sr, n_mfcc=40):
    """
    Extracts MFCC features from audio.

    Returns:
        mfcc: (n_mfcc, time_steps) array.
    """
    if y is None or sr is None:
        return None
    # Extract MFCC and standardize per file
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    return mfcc

def plot_audio(y, sr, title="Audio Analysis"):
    """Plots waveform and spectrogram of the audio signal."""
    if y is None or sr is None:
        print("Invalid audio data!")
        return
    plt.figure(figsize=(12, 8))
    # Waveform
    plt.subplot(2,1,1)
    librosa.display.waveshow(y, sr=sr)
    plt.title("Waveform")
    # Spectrogram
    plt.subplot(2,1,2)
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
    plt.title("Spectrogram")
    plt.colorbar(format="%+2.0f dB")

    plt.suptitle(title, fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

# Test on a sample audio file (update the path)
sample_file = "/content/drive/MyDrive/snorıng1/Horlama/10.wav"  # Replace with your audio file path
y, sr = load_audio(sample_file, duration=5.0)
plot_audio(y, sr, title="Sample Audio Analysis")

def extract_features(file_path, duration=10.0, n_mfcc=40, max_len=431):  # max_len = تقريب عدد الفريمات لـ 10 ثواني
    try:
        y, sr = librosa.load(file_path, duration=duration)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        # ملء المصفوفة إذا كانت أقصر من max_len
        if mfcc.shape[1] < max_len:
            pad_width = max_len - mfcc.shape[1]
            mfcc = np.pad(mfcc, pad_width=((0, 0), (0, pad_width)), mode='constant')
        else:
            mfcc = mfcc[:, :max_len]  # قصها لو أطول
        return mfcc
    except Exception as e:
        print(f"خطأ في الملف {file_path}: {e}")
        return None

def load_dataset(snore_dir, non_snore_dir, duration=10.0, n_mfcc=20):
    X = []
    y = []

    for filename in os.listdir(snore_dir):
        if filename.endswith(".wav"):
            path = os.path.join(snore_dir, filename)
            mfcc = extract_features(path, duration=duration, n_mfcc=n_mfcc)
            if mfcc is not None:
                X.append(mfcc)
                y.append(1)

    for filename in os.listdir(non_snore_dir):
        if filename.endswith(".wav"):
            path = os.path.join(non_snore_dir, filename)
            mfcc = extract_features(path, duration=duration, n_mfcc=n_mfcc)
            if mfcc is not None:
                X.append(mfcc)
                y.append(0)

    return np.array(X), np.array(y)


# Update these directories to your dataset paths
snore_directory = "/content/drive/MyDrive/snorıng1/Horlama"
non_snore_directory = "/content/drive/MyDrive/snorıng1/Horlama olmayan"

X, y = load_dataset(snore_directory, non_snore_directory, duration=10.0, n_mfcc=40)
print("Dataset shapes:", X.shape, y.shape)

def pad_features(mfccs, max_len=216):
    """
    Pads or truncates MFCC arrays (shape: n_mfcc x time_steps) so that they all have the same time dimension.
    """
    padded = []
    for mfcc in mfccs:
        if mfcc.shape[1] < max_len:
            pad_width = max_len - mfcc.shape[1]
            mfcc = np.pad(mfcc, pad_width=((0, 0), (0, pad_width)), mode='constant')
        else:
            mfcc = mfcc[:, :max_len]
        padded.append(mfcc)
    return np.array(padded)

# You can decide the fixed length based on your data (216 here is an example)
fixed_length = 216
X_padded = pad_features(X, max_len=fixed_length)
print("Padded dataset shape:", X_padded.shape)

X_ready = X_padded[..., np.newaxis]  # shape becomes (n_samples, n_mfcc, time, 1)
print("Input shape for CNN:", X_ready.shape)

X_train, X_test, y_train, y_test = train_test_split(X_ready, y, test_size=0.2, random_state=42, stratify=y)
print("Train set:", X_train.shape, "Test set:", X_test.shape)

# Flatten the data for scaling (preserving the conv shape can be restored later)
X_train_flat = X_train.reshape(X_train.shape[0], -1)
X_test_flat = X_test.reshape(X_test.shape[0], -1)

scaler = StandardScaler()
X_train_flat_scaled = scaler.fit_transform(X_train_flat)
X_test_flat_scaled = scaler.transform(X_test_flat)

# Reshape back to the original shape for CNN input
X_train_scaled = X_train_flat_scaled.reshape(X_train.shape)
X_test_scaled = X_test_flat_scaled.reshape(X_test.shape)

# Save the scaler to disk for later use during inference
scaler_save_path = 'scaler.pkl'
with open(scaler_save_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"Scaler saved to {scaler_save_path}")

def create_tiny_cnn(input_shape):
    model = models.Sequential([
        layers.Conv2D(16, (3, 3), activation='relu', input_shape=input_shape),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),

        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(1, activation='sigmoid')  # Single output with sigmoid for binary classification
    ])

    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    return model

input_shape = X_train_scaled.shape[1:]  # (n_mfcc, fixed_length, 1)
model = create_tiny_cnn(input_shape)
model.summary()

early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

history = model.fit(
    X_train_scaled, y_train,
    epochs=50,
    batch_size=16,
    validation_split=0.2,
    callbacks=[early_stop]
)

plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Val Accuracy')
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.title("Training and Validation Accuracy")
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training and Validation Loss")
plt.legend()
plt.show()

y_pred_probs = model.predict(X_test_scaled)
y_pred = (y_pred_probs > 0.5).astype(int).flatten()

cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Non-Snore", "Snore"])
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.show()

model_save_path = "tiny_cnn_snoring_detector.h5"
model.save(model_save_path)
print(f"Model saved to {model_save_path}")

import sounddevice as sd
import numpy as np
import librosa
import pickle
import tensorflow as tf
import queue
import time


model = tf.keras.models.load_model('tiny_cnn_snoring_detector.h5')
with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)


sample_rate = 22050
duration = 10.0
n_mfcc = 40
fixed_length = 216
threshold = 0.5


audio_queue = queue.Queue()


def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())


def detect_snoring(audio_data):

    mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)


    if mfcc.shape[1] < fixed_length:
        pad_width = fixed_length - mfcc.shape[1]
        mfcc = np.pad(mfcc, pad_width=((0, 0), (0, pad_width)), mode='constant')
    else:
        mfcc = mfcc[:, :fixed_length]


    mfcc = mfcc[..., np.newaxis]
    input_data = np.expand_dims(mfcc, axis=0)


    input_flat = input_data.reshape(1, -1)
    input_scaled_flat = scaler.transform(input_flat)
    input_scaled = input_scaled_flat.reshape(input_data.shape)


    probability = model.predict(input_scaled)[0][0]
    return probability


def main():
    stream = sd.InputStream(channels=1, samplerate=sample_rate, callback=audio_callback)
    stream.start()
    print(" Anlık horlama tespiti başladı (durdurmak için Ctrl+C tuşlayın)")

    try:
        while True:
            audio_frames = []
            start_time = time.time()

            while time.time() - start_time < duration:
                try:
                    data = audio_queue.get(timeout=duration)
                    audio_frames.append(data)
                except queue.Empty:
                    break

            if audio_frames:
                audio_chunk = np.concatenate(audio_frames, axis=0).flatten()
                prob = detect_snoring(audio_chunk)

                if prob > threshold:
                    print(f" Horlama tespit edildi! (olasılık: {prob:.2f})")
                else:
                    print(f"Horlama yok. (olasılık: {prob:.2f})")
            else:
                print(" Ses algılanmadı.")
    except KeyboardInterrupt:
        print("Algılama kullanıcı tarafından durduruldu.")
    finally:
        stream.stop()
        stream.close()


if __name__ == "__main__":
    main()