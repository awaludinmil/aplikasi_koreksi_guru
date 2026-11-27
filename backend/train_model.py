"""
================================================================================
SCRIPT TRAINING CNN RESNET50 TRANSFER LEARNING (KERAS / TENSORFLOW)
================================================================================
Dataset : Klasifikasi Gambar (2 Kelas: terpilih / tidak_terpilih)
Tujuan  : Melatih model CNN ResNet50 dengan bobot ImageNet & Fine-Tuning.

--------------------------------------------------------------------------------
PANDUAN / CARA MENJALANKAN TRAINING ULANG:
--------------------------------------------------------------------------------

1. Buka Terminal (PowerShell atau Command Prompt di Windows).

2. Masuk ke direktori backend:
   cd c:\\Users\\fauza\\Documents\\Kuliah\\semester-7\\PPAS\\skripsi_awal\\backend

3. Aktifkan Virtual Environment:
   - Windows PowerShell : .\\venv\\Scripts\\Activate.ps1
   - Windows CMD        : .\\venv\\Scripts\\activate.bat
   - Linux/Mac          : source venv/bin/activate

4. Menjalankan Training Standar (Rekomendasi Default):
   python train_model.py

5. Menjalankan Training dengan Kustomisasi Hyperparameter (Opsional):
   python train_model.py --phase1_epochs 15 --phase2_epochs 30 --batch_size 16 --lr_phase1 0.001 --lr_phase2 0.00001

6. Menjalankan Inferensi / Prediksi Gambar Tunggal (Testing):
   python train_model.py --predict "path/ke/file_gambar.jpg"
   Contoh:
   python train_model.py --predict "../Klasifikasi.v1i.folder/test/terpilih/IMG_xxxx.jpg"

--------------------------------------------------------------------------------
OUTPUT FILE YANG DIHASILKAN DI FOLDER 'model_output/':
--------------------------------------------------------------------------------
- best_model.keras       : Model terbaik (berdasarkan validation loss terendah)
- final_model.keras      : Model akhir setelah seluruh epoch selesai
- class_indices.json     : Mapping label kelas {'terpilih': 0, 'tidak_terpilih': 1}
- training_log.csv       : Riwayat training per-epoch (loss, acc, val_loss, val_acc)
- accuracy_loss_plot.png : Grafik kurva Akurasi dan Loss (Phase 1 + Phase 2)
- confusion_matrix.png   : Visualisasi Confusion Matrix dengan Matplotlib murni
- roc_curve.png          : Kurva ROC dan skor AUC pada data test
- training_report.txt    : Laporan metrics lengkap (Precision, Recall, F1-Score)
================================================================================
"""

import os
import sys
import json
import argparse
import itertools
import numpy as np

# Matplotlib configuration (Non-interactive Agg backend untuk server & CLI)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve

import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks, regularizers
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input


def parse_args():
    """
    Mengurai argumen command line untuk kustomisasi training.
    """
    parser = argparse.ArgumentParser(
        description="Script Training ResNet50 untuk Klasifikasi Gambar Biner (terpilih vs tidak_terpilih)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--dataset_dir",
        type=str,
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Klasifikasi.v1i.folder")),
        help="Path ke folder root dataset yang berisi subfolder train, valid, test"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "model_output")),
        help="Path folder untuk menyimpan output model, grafik matplotlib, dan laporan"
    )
    parser.add_argument("--img_size", type=int, default=224, help="Ukuran resolusi gambar input (default: 224x224)")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size training")
    parser.add_argument("--phase1_epochs", type=int, default=10, help="Jumlah epoch Phase 1 (Transfer Learning head)")
    parser.add_argument("--phase2_epochs", type=int, default=25, help="Jumlah epoch Phase 2 (Fine-tuning)")
    parser.add_argument("--lr_phase1", type=float, default=1e-3, help="Learning rate Phase 1")
    parser.add_argument("--lr_phase2", type=float, default=1e-5, help="Learning rate Phase 2")
    parser.add_argument("--predict", type=str, default=None, help="Path file gambar jika ingin menjalankan mode inferensi")
    return parser.parse_args()


def load_dataset(dataset_dir, img_size, batch_size):
    """
    Memuat dataset train, valid, dan test dari struktur folder.
    """
    train_dir = os.path.join(dataset_dir, "train")
    valid_dir = os.path.join(dataset_dir, "valid")
    test_dir = os.path.join(dataset_dir, "test")

    for p in [train_dir, valid_dir, test_dir]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Direktori dataset tidak ditemukan: {p}")

    print("=" * 70)
    print(f"MEMUAT DATASET DARI: {dataset_dir}")
    print("=" * 70)

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        image_size=(img_size, img_size),
        batch_size=batch_size,
        label_mode="binary",
        shuffle=True,
        seed=42
    )

    class_names = train_ds.class_names
    print(f"Kelas yang ditemukan: {class_names}")

    valid_ds = tf.keras.utils.image_dataset_from_directory(
        valid_dir,
        image_size=(img_size, img_size),
        batch_size=batch_size,
        label_mode="binary",
        shuffle=False
    )

    test_ds = tf.keras.utils.image_dataset_from_directory(
        test_dir,
        image_size=(img_size, img_size),
        batch_size=batch_size,
        label_mode="binary",
        shuffle=False
    )

    # Preprocessing pipeline dengan preprocess_input ResNet50
    train_ds = train_ds.map(lambda x, y: (preprocess_input(x), y), num_parallel_calls=tf.data.AUTOTUNE)
    valid_ds = valid_ds.map(lambda x, y: (preprocess_input(x), y), num_parallel_calls=tf.data.AUTOTUNE)
    test_ds = test_ds.map(lambda x, y: (preprocess_input(x), y), num_parallel_calls=tf.data.AUTOTUNE)

    return train_ds, valid_ds, test_ds, class_names


def calculate_class_weights(dataset_dir, class_names):
    """
    Menghitung class weights otomatis untuk mengatasi ketidakseimbangan data.
    """
    train_dir = os.path.join(dataset_dir, "train")
    counts = {}
    for idx, c_name in enumerate(class_names):
        c_path = os.path.join(train_dir, c_name)
        if os.path.isdir(c_path):
            counts[idx] = len([f for f in os.listdir(c_path) if os.path.isfile(os.path.join(c_path, f))])
        else:
            counts[idx] = 0

    total = sum(counts.values())
    n_classes = len(class_names)
    class_weights = {}

    print(f"\nDistribusi Jumlah Sampel Training:")
    for idx, c_name in enumerate(class_names):
        count = counts.get(idx, 0)
        weight = total / (n_classes * count) if count > 0 else 1.0
        class_weights[idx] = weight
        print(f" - [{idx}] {c_name:15s}: {count:4d} gambar | Bobot Class Weight: {weight:.4f}")

    return class_weights


def build_model(img_size=(224, 224)):
    """
    Membangun arsitektur model CNN ResNet50 Transfer Learning:
    1. Input layer (224, 224, 3)
    2. Pretrained ResNet50 Base (ImageNet)
    3. Custom Head: GlobalAvgPool + BatchNorm + Dense(256) + Dropout(0.5) + Dense(64) + Dropout(0.3) + Dense(1, sigmoid)
    """
    inputs = layers.Input(shape=(img_size[0], img_size[1], 3), name="input_image")
    
    # Base Model ResNet50 pretrained weights ImageNet
    base_model = ResNet50(
        weights="imagenet",
        include_top=False,
        input_tensor=inputs
    )
    base_model.trainable = False  # Bekukan base model untuk Phase 1

    # Custom Top Classification Head
    x = base_model.output
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.BatchNormalization(name="head_bn")(x)
    x = layers.Dense(256, activation="relu", kernel_regularizer=regularizers.l2(1e-4), name="head_dense1")(x)
    x = layers.Dropout(0.5, name="head_dropout1")(x)
    x = layers.Dense(64, activation="relu", name="head_dense2")(x)
    x = layers.Dropout(0.3, name="head_dropout2")(x)
    outputs = layers.Dense(1, activation="sigmoid", name="output_prediction")(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="ResNet50_Classifier")
    return model, base_model


def plot_training_history_matplotlib(history_phase1, history_phase2, output_dir):
    """
    Membuat grafik visualisasi training loss dan accuracy menggunakan Matplotlib murni.
    """
    acc = history_phase1.history.get("accuracy", [])
    val_acc = history_phase1.history.get("val_accuracy", [])
    loss = history_phase1.history.get("loss", [])
    val_loss = history_phase1.history.get("val_loss", [])

    if history_phase2:
        acc += history_phase2.history.get("accuracy", [])
        val_acc += history_phase2.history.get("val_accuracy", [])
        loss += history_phase2.history.get("loss", [])
        val_loss += history_phase2.history.get("val_loss", [])

    epochs_range = range(1, len(acc) + 1)
    phase1_len = len(history_phase1.history.get("accuracy", []))

    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5), dpi=300)

    # ------------------ SUBPLOT 1: AKURASI ------------------
    ax1.plot(epochs_range, acc, label="Training Accuracy", color="#1d4ed8", lw=2.2, marker="o", markersize=3)
    ax1.plot(epochs_range, val_acc, label="Validation Accuracy", color="#15803d", lw=2.2, marker="s", markersize=3)
    if history_phase2 and phase1_len < len(acc):
        ax1.axvline(x=phase1_len, color="#b91c1c", linestyle="--", lw=1.8, label="Start Fine-Tuning")
    
    ax1.set_title("Grafik Training & Validation Accuracy", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Epoch", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("Akurasi", fontsize=11, fontweight="semibold")
    ax1.set_ylim([0, 1.05])
    ax1.legend(loc="lower right", frameon=True, framealpha=0.9)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # ------------------ SUBPLOT 2: LOSS ------------------
    ax2.plot(epochs_range, loss, label="Training Loss", color="#1d4ed8", lw=2.2, marker="o", markersize=3)
    ax2.plot(epochs_range, val_loss, label="Validation Loss", color="#15803d", lw=2.2, marker="s", markersize=3)
    if history_phase2 and phase1_len < len(loss):
        ax2.axvline(x=phase1_len, color="#b91c1c", linestyle="--", lw=1.8, label="Start Fine-Tuning")
    
    ax2.set_title("Grafik Training & Validation Loss", fontsize=13, fontweight="bold", pad=12)
    ax2.set_xlabel("Epoch", fontsize=11, fontweight="semibold")
    ax2.set_ylabel("Loss", fontsize=11, fontweight="semibold")
    ax2.legend(loc="upper right", frameon=True, framealpha=0.9)
    ax2.grid(True, linestyle="--", alpha=0.4)

    plt.suptitle("Evaluasi Proses Training ResNet50 (Transfer Learning & Fine-Tuning)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, "accuracy_loss_plot.png")
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[MATPLOTLIB] Grafik riwayat training disimpan di: {plot_path}")


def plot_confusion_matrix_matplotlib(cm, class_names, output_dir):
    """
    Membuat visualisasi Confusion Matrix elegan menggunakan Matplotlib murni.
    """
    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    
    # Visualisasi matriks dengan colormap Blues
    cax = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    cbar = fig.colorbar(cax, fraction=0.046, pad=0.04)
    cbar.set_label("Jumlah Sampel", rotation=270, labelpad=15, fontsize=10, fontweight="semibold")

    # Tick marks dan label
    tick_marks = np.arange(len(class_names))
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(class_names, fontsize=11, fontweight="semibold")
    ax.set_yticklabels(class_names, fontsize=11, fontweight="semibold")

    # Hitung threshold kontras warna teks
    thresh = cm.max() / 2.0
    total_samples = np.sum(cm)

    labels_desc = [
        ["True Negative (TN)", "False Positive (FP)"],
        ["False Negative (FN)", "True Positive (TP)"]
    ]

    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        val = cm[i, j]
        pct = (val / total_samples) * 100 if total_samples > 0 else 0
        desc = labels_desc[i][j] if i < 2 and j < 2 else ""
        text_color = "white" if val > thresh else "black"

        cell_text = f"{val}\n({pct:.1f}%)\n{desc}"
        ax.text(
            j, i, cell_text,
            horizontalalignment="center",
            verticalalignment="center",
            color=text_color,
            fontsize=10,
            fontweight="bold"
        )

    ax.set_title("Confusion Matrix (Test Set)\nModel ResNet50 Classifier", fontsize=13, fontweight="bold", pad=15)
    ax.set_ylabel("True Label (Aktual)", fontsize=11, fontweight="semibold")
    ax.set_xlabel("Predicted Label (Prediksi)", fontsize=11, fontweight="semibold")

    plt.tight_layout()
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[MATPLOTLIB] Confusion Matrix disimpan di: {cm_path}")


def evaluate_and_report(model, test_ds, class_names, output_dir):
    """
    Evaluasi model pada data test dan simpan confusion matrix, ROC curve, dan classification report.
    """
    print("\n" + "=" * 70)
    print("MENGEVALUASI MODEL PADA TEST SET...")
    print("=" * 70)

    y_true = []
    y_pred_probs = []

    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy().flatten())
        y_pred_probs.extend(preds.flatten())

    y_true = np.array(y_true, dtype=int)
    y_pred_probs = np.array(y_pred_probs)
    y_pred = (y_pred_probs >= 0.5).astype(int)

    # 1. Classification Report
    report_str = classification_report(y_true, y_pred, target_names=class_names, digits=4)
    print("\n--- CLASSIFICATION REPORT (DATA TEST) ---")
    print(report_str)

    # 2. Confusion Matrix dengan Matplotlib
    cm = confusion_matrix(y_true, y_pred)
    plot_confusion_matrix_matplotlib(cm, class_names, output_dir)

    # 3. ROC Curve & AUC dengan Matplotlib
    auc_score = 0.0
    try:
        auc_score = roc_auc_score(y_true, y_pred_probs)
        fpr, tpr, _ = roc_curve(y_true, y_pred_probs)

        fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=300)
        ax.plot(fpr, tpr, color="#2563eb", lw=2.5, label=f"ResNet50 (AUC = {auc_score:.4f})")
        ax.plot([0, 1], [0, 1], color="#9ca3af", linestyle="--", lw=1.5, label="Random Classifier (AUC = 0.5000)")
        ax.set_title("Receiver Operating Characteristic (ROC) Curve", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="semibold")
        ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11, fontweight="semibold")
        ax.legend(loc="lower right", frameon=True)
        ax.grid(True, linestyle="--", alpha=0.4)
        
        plt.tight_layout()
        roc_path = os.path.join(output_dir, "roc_curve.png")
        plt.savefig(roc_path, bbox_inches="tight")
        plt.close(fig)
        print(f"[MATPLOTLIB] ROC Curve disimpan di: {roc_path}")
    except Exception as e:
        print(f"[WARNING] Gagal membuat kurva ROC: {e}")

    # 4. Simpan Ringkasan ke File Text
    report_file_path = os.path.join(output_dir, "training_report.txt")
    with open(report_file_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("LAPORAN EVALUASI MODEL RESNET50 (TEST SET)\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Class Names : {class_names}\n")
        f.write(f"ROC-AUC     : {auc_score:.4f}\n\n")
        f.write("Confusion Matrix:\n")
        f.write(str(cm) + "\n\n")
        f.write("Classification Report:\n")
        f.write(report_str + "\n")

    print(f"Laporan ringkasan disimpan di: {report_file_path}")


def run_prediction(image_path, model_path, output_dir):
    """
    Menjalankan inferensi pada single image untuk pengujian langsung.
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] File gambar tidak ditemukan: {image_path}")
        return

    if not os.path.exists(model_path):
        print(f"[ERROR] File model tidak ditemukan: {model_path}")
        return

    # Load class mapping
    indices_file = os.path.join(output_dir, "class_indices.json")
    if os.path.exists(indices_file):
        with open(indices_file, "r") as f:
            class_indices = json.load(f)
        class_names = {v: k for k, v in class_indices.items()}
    else:
        class_names = {0: "terpilih", 1: "tidak_terpilih"}

    print(f"\nMemuat model dari: {model_path}")
    model = tf.keras.models.load_model(model_path)

    img = tf.keras.utils.load_img(image_path, target_size=(224, 224))
    img_array = tf.keras.utils.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    prob = float(model.predict(img_array, verbose=0)[0][0])
    pred_idx = 1 if prob >= 0.5 else 0
    pred_label = class_names.get(pred_idx, f"Class {pred_idx}")
    confidence = prob if pred_idx == 1 else (1.0 - prob)

    print("\n" + "=" * 60)
    print("HASIL PREDIKSI GAMBAR:")
    print("=" * 60)
    print(f"File Gambar : {image_path}")
    print(f"Prediksi    : {pred_label.upper()}")
    print(f"Confidence  : {confidence * 100:.2f}% (Probabilitas sigmoid raw: {prob:.4f})")
    print("=" * 60)


def main():
    args = parse_args()

    # Mode Prediksi / Inferensi
    if args.predict:
        best_model_path = os.path.join(args.output_dir, "best_model.keras")
        run_prediction(args.predict, best_model_path, args.output_dir)
        return

    os.makedirs(args.output_dir, exist_ok=True)

    # 1. Memuat Dataset
    train_ds, valid_ds, test_ds, class_names = load_dataset(
        args.dataset_dir, args.img_size, args.batch_size
    )

    # Simpan mapping kelas ke JSON
    class_indices = {name: idx for idx, name in enumerate(class_names)}
    with open(os.path.join(args.output_dir, "class_indices.json"), "w") as f:
        json.dump(class_indices, f, indent=2)

    # 2. Hitung Class Weights
    class_weights = calculate_class_weights(args.dataset_dir, class_names)

    # Optimasi I/O pipeline dengan cache & prefetch
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    valid_ds = valid_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # 3. Membangun Model
    print("\n" + "=" * 70)
    print("MEMBANGUN MODEL RESNET50...")
    print("=" * 70)
    model, base_model = build_model(img_size=(args.img_size, args.img_size))
    model.summary()

    # Callbacks Konfigurasi
    best_model_path = os.path.join(args.output_dir, "best_model.keras")
    final_model_path = os.path.join(args.output_dir, "final_model.keras")
    log_csv_path = os.path.join(args.output_dir, "training_log.csv")

    callback_list_p1 = [
        callbacks.ModelCheckpoint(
            filepath=best_model_path,
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=1
        ),
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
            verbose=1
        ),
        callbacks.CSVLogger(log_csv_path, append=False)
    ]

    # =========================================================================
    # PHASE 1: Feature Extraction (Base Model ResNet50 Frozen)
    # =========================================================================
    print("\n" + "=" * 70)
    print(f"MEMULAI PHASE 1: Training Head ({args.phase1_epochs} Epochs, LR={args.lr_phase1})")
    print("=" * 70)

    model.compile(
        optimizer=optimizers.Adam(learning_rate=args.lr_phase1),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc")
        ]
    )

    history_p1 = model.fit(
        train_ds,
        validation_data=valid_ds,
        epochs=args.phase1_epochs,
        class_weight=class_weights,
        callbacks=callback_list_p1
    )

    # =========================================================================
    # PHASE 2: Fine-Tuning (Unfreeze Top Layers ResNet50)
    # =========================================================================
    print("\n" + "=" * 70)
    print("MEMULAI PHASE 2: Fine-Tuning ResNet50 Top Layers")
    print("=" * 70)

    base_model.trainable = True
    # Freeze lower layers, hanya unfreeze top 40 layers
    fine_tune_at = len(base_model.layers) - 40
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False

    print(f"Total layers pada ResNet50 base: {len(base_model.layers)}")
    print(f"Jumlah trainable variables: {len(model.trainable_variables)}")

    model.compile(
        optimizer=optimizers.Adam(learning_rate=args.lr_phase2),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc")
        ]
    )

    callback_list_p2 = [
        callbacks.ModelCheckpoint(
            filepath=best_model_path,
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=1
        ),
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=7,
            restore_best_weights=True,
            verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),
        callbacks.CSVLogger(log_csv_path, append=True)
    ]

    history_p2 = model.fit(
        train_ds,
        validation_data=valid_ds,
        epochs=args.phase1_epochs + args.phase2_epochs,
        initial_epoch=len(history_p1.history["loss"]),
        class_weight=class_weights,
        callbacks=callback_list_p2
    )

    # Simpan model final
    model.save(final_model_path)
    print(f"\nModel final tersimpan di: {final_model_path}")

    # 4. Plot History Kurva Akurasi & Loss dengan Matplotlib
    plot_training_history_matplotlib(history_p1, history_p2, args.output_dir)

    # 5. Evaluasi pada Test Set menggunakan Model Terbaik
    if os.path.exists(best_model_path):
        print(f"\nMemuat model terbaik dari: {best_model_path}")
        best_model = tf.keras.models.load_model(best_model_path)
        evaluate_and_report(best_model, test_ds, class_names, args.output_dir)
    else:
        evaluate_and_report(model, test_ds, class_names, args.output_dir)

    print("\n" + "=" * 70)
    print("TRAINING & EVALUASI SELESAI DENGAN SUKSES!")
    print(f"Semua hasil tersimpan di folder: {args.output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
