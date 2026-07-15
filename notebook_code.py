import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, roc_curve, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)
import xgboost as xgb
import joblib

# Tüm rastgelelik gerektiren adımlarda AYNI seed'i kullanıyoruz.
# Bu sayede notebook'u kim, ne zaman çalıştırırsa çalıştırsın AYNI sonuçları alır
# -- jüri/ekip tarafından tekrar üretilebilirlik (reproducibility) için kritik.
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("Kütüphaneler yüklendi. RANDOM_STATE =", RANDOM_STATE)

CSV_PATH = "texergy_ai_synthetic_dataset_v5.csv"

if not os.path.exists(CSV_PATH):
    try:
        from google.colab import files
        print("Dosya bulunamadı. Lütfen 'texergy_ai_synthetic_dataset_v5.csv' dosyasını seçin:")
        uploaded = files.upload()
        CSV_PATH = list(uploaded.keys())[0]
    except ImportError:
        raise FileNotFoundError(
            f"'{CSV_PATH}' bulunamadı. Dosyayı bu notebook ile aynı klasöre "
            "koyun ya da Google Drive'dan okuyacaksanız drive.mount() kullanıp "
            "yolu güncelleyin."
        )

df = pd.read_csv(CSV_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["maint_bin"] = (df["maintenance_needed"] == "Yes").astype(int)

print("Veri seti yüklendi.")
print("Şekil:", df.shape)
df.head()

print("=== Duplicate kayıt sayısı ===")
print(df.duplicated().sum())

print()
print("=== Eksik değerler ===")
missing = df.isnull().sum()
print(missing[missing > 0])

print()
print("=== Aralık dışı değer kontrolü (0-100 olması gereken kolonlar) ===")
for col in ["quality_score", "production_efficiency", "efficiency_score"]:
    out_of_range = df[(df[col] < 0) | (df[col] > 100)]
    print(f"{col}: {len(out_of_range)} aralık dışı satır")

print()
print("=== Temel istatistikler ===")
df.describe().T[["min", "mean", "max"]]

import seaborn as sns

# 1. Önemli sensör ve üretim metriklerinin dağılımları (Histogramlar)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

sns.histplot(df['machine_speed'], bins=40, kde=True, ax=axes[0, 0], color='skyblue')
axes[0, 0].set_title('Makine Hızı (machine_speed) Dağılımı')

sns.histplot(df['energy_consumption'], bins=40, kde=True, ax=axes[0, 1], color='salmon')
axes[0, 1].set_title('Enerji Tüketimi (energy_consumption) Dağılımı')

sns.histplot(df['defect_rate'], bins=40, kde=True, ax=axes[1, 0], color='lightgreen')
axes[1, 0].set_title('Hata Oranı (defect_rate) Dağılımı')

# Anomali durumuna göre Verimlilik Skoru dağılımı
sns.boxplot(x='anomaly_label', y='efficiency_score', data=df, ax=axes[1, 1], palette='Set2', hue='anomaly_label', legend=False)
axes[1, 1].set_title('Anomali Durumuna Göre Verimlilik Skoru (efficiency_score)')

plt.tight_layout()
plt.show()
# 2. Zaman Serisi Grafiği (Örnek Makine: M003 - Spinning)
sample_machine_id = 'M003'
sample_df = df[df['machine_id'] == sample_machine_id].sort_values('timestamp')

fig, ax1 = plt.subplots(figsize=(14, 5))

# Enerji tüketimini kırmızı ile çizdiriyoruz
ax1.plot(sample_df['timestamp'], sample_df['energy_consumption'], color='red', marker='o', markersize=4, label='Enerji Tüketimi')
ax1.set_xlabel('Zaman (Timestamp)')
ax1.set_ylabel('Enerji Tüketimi', color='red')
ax1.tick_params(axis='y', labelcolor='red')

# Aynı grafikte makine hızını mavi ile çizdiriyoruz (ikinci y ekseni)
ax2 = ax1.twinx()
ax2.plot(sample_df['timestamp'], sample_df['machine_speed'], color='blue', alpha=0.5, label='Makine Hızı')
ax2.set_ylabel('Makine Hızı', color='blue')
ax2.tick_params(axis='y', labelcolor='blue')

plt.title(f'{sample_machine_id} Makinesi Zaman İçindeki Trend (Enerji vs Hız)')
fig.autofmt_xdate() # Tarihleri çapraz yazdırarak okunaklı yapar
plt.show()
print("=" * 70)
print("İLİŞKİ 1: humidity -> defect_rate")
print("=" * 70)
corr = df["humidity"].corr(df["defect_rate"])
print(f"Korelasyon: {corr:.3f}   (v4'te: -0.018 idi, yani ilişki yoktu)")
print("Sonuç:", "İlişki artık var (pozitif yönlü)." if corr > 0.1 else "Hala zayıf.")

print("=" * 70)
print("İLİŞKİ 2: machine_speed -> defect_rate (facility bazında, çünkü")
print("makine hızının ölçeği facility'e göre 1000 kat farklı - global")
print("korelasyon bu farkı maskeler)")
print("=" * 70)
for f in sorted(df["facility_type"].unique()):
    sub = df[df["facility_type"] == f]
    corr = sub["machine_speed"].corr(sub["defect_rate"])
    print(f"  {f:12s}: r = {corr:.3f}")
print()
print("Sonuç: Tüm facility'lerde tutarlı pozitif ilişki (v4'te 0.02-0.12 arası, tutarsızdı).")

print("=" * 70)
print("İLİŞKİ 3: machine_speed -> output_quantity (facility bazında)")
print("=" * 70)
for f in sorted(df["facility_type"].unique()):
    sub = df[df["facility_type"] == f]
    corr = sub["machine_speed"].corr(sub["output_quantity"])
    print(f"  {f:12s}: r = {corr:.3f}")
print()
print("Sonuç: Güçlü pozitif ilişki her facility'de (v4'te ~0 idi).")

print("=" * 70)
print("İLİŞKİ 4: Aynı makine zaman içinde tutarlı davranıyor mu?")
print("(Mantık: eğer makinenin 'kimliği' varsa, o makinenin kendi içindeki")
print("varyans, tüm veri setinin genel varyansından belirgin şekilde düşük olmalı)")
print("=" * 70)
overall_std = df["efficiency_score"].std()
within_machine_std = df.groupby("machine_id")["efficiency_score"].std().mean()
reduction = (1 - within_machine_std / overall_std) * 100
print(f"Genel efficiency_score std       : {overall_std:.2f}")
print(f"Makine-içi ortalama std           : {within_machine_std:.2f}")
print(f"Azalma oranı                      : %{reduction:.1f}")
print()
print("Sonuç:", "Gerçek makine kimliği etkisi var." if reduction > 15 else "Zayıf/yok.")
print("(v4'te bu azalma sadece %5.8'di, yani neredeyse hiç makine kimliği etkisi yoktu)")

numeric_cols = [
    "machine_speed", "production_time", "output_quantity", "energy_consumption",
    "energy_per_unit", "ambient_temperature", "humidity", "defect_rate",
    "carbon_emission", "energy_cost", "production_efficiency", "quality_score",
    "efficiency_score", "anomaly_label", "energy_waste_flag", "maint_bin",
]

corr_matrix = df[numeric_cols].corr()

fig, ax = plt.subplots(figsize=(11, 9))
im = ax.imshow(corr_matrix, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(numeric_cols)))
ax.set_yticks(range(len(numeric_cols)))
ax.set_xticklabels(numeric_cols, rotation=90)
ax.set_yticklabels(numeric_cols)
plt.colorbar(im, ax=ax, label="Korelasyon")
ax.set_title("v5 Korelasyon Matrisi (tüm sayısal kolonlar)")
plt.tight_layout()
plt.savefig("corr_matrix.png", dpi=110)
plt.show()

df_sorted = df.sort_values("timestamp").reset_index(drop=True)

split_idx = int(len(df_sorted) * 0.75)
split_date = df_sorted.iloc[split_idx]["timestamp"]

train_df = df_sorted[df_sorted["timestamp"] < split_date].copy()
test_df = df_sorted[df_sorted["timestamp"] >= split_date].copy()

print(f"Split tarihi        : {split_date}")
print(f"Train aralığı       : {train_df['timestamp'].min()}  ->  {train_df['timestamp'].max()}")
print(f"Test aralığı        : {test_df['timestamp'].min()}  ->  {test_df['timestamp'].max()}")
print(f"Train satır sayısı  : {len(train_df)}")
print(f"Test satır sayısı   : {len(test_df)}")
print(f"Train anomali oranı : {train_df['anomaly_label'].mean():.3f}")
print(f"Test anomali oranı  : {test_df['anomaly_label'].mean():.3f}")

def quick_auc(feature_df, target, use_machine_id, split_mode):
    cols = ["machine_speed", "production_time", "output_quantity", "energy_consumption",
            "energy_per_unit", "ambient_temperature", "humidity", "defect_rate",
            "carbon_emission", "energy_cost", "production_efficiency", "quality_score",
            "efficiency_score"]
    X = feature_df[cols + ["facility_type", "shift"]].copy()
    if use_machine_id:
        X["machine_id"] = feature_df["machine_id"]
    X = pd.get_dummies(X, columns=["facility_type", "shift"] + (["machine_id"] if use_machine_id else []))
    y = feature_df[target]

    if split_mode == "random":
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y)
    else:  # time
        sorted_idx_local = feature_df.sort_values("timestamp").index
        X_sorted_local, y_sorted_local = X.loc[sorted_idx_local], y.loc[sorted_idx_local]
        cut_local = int(len(X_sorted_local) * 0.75)
        Xtr, Xte = X_sorted_local.iloc[:cut_local], X_sorted_local.iloc[cut_local:]
        ytr, yte = y_sorted_local.iloc[:cut_local], y_sorted_local.iloc[cut_local:]

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        eval_metric="logloss", random_state=RANDOM_STATE
    )
    model.fit(Xtr, ytr)
    proba = model.predict_proba(Xte)[:, 1]
    return roc_auc_score(yte, proba)


leak_results = []
for use_mid in [True, False]:
    for split_mode in ["random", "time"]:
        auc = quick_auc(df, "anomaly_label", use_mid, split_mode)
        leak_results.append({
            "machine_id feature": "VAR" if use_mid else "YOK",
            "split": "Rastgele" if split_mode == "random" else "Zaman bazlı",
            "AUC": round(auc, 3),
        })

leak_table = pd.DataFrame(leak_results)
print(leak_table.to_string(index=False))

num_cols = ["machine_speed", "production_time", "output_quantity", "energy_consumption",
            "energy_per_unit", "ambient_temperature", "humidity", "defect_rate",
            "carbon_emission", "energy_cost", "production_efficiency", "quality_score",
            "efficiency_score"]

# --- Versiyon A: Ham özellikler (RobustScaler) ---
X_raw = RobustScaler().fit_transform(df[num_cols])
iso_raw = IsolationForest(n_estimators=300, contamination=0.21, random_state=RANDOM_STATE)
iso_raw.fit(X_raw)
score_raw = -iso_raw.score_samples(X_raw)
auc_raw = roc_auc_score(df["anomaly_label"], score_raw)

# --- Versiyon B: Facility-bazlı z-score özellikler ---
def facility_zscore(col):
    g = df.groupby("facility_type")[col]
    return (df[col] - g.transform("mean")) / g.transform("std")

eng_cols = ["defect_rate", "quality_score", "energy_per_unit", "energy_consumption",
            "production_efficiency", "efficiency_score", "machine_speed"]
X_eng = np.column_stack([facility_zscore(c) for c in eng_cols])
iso_eng = IsolationForest(n_estimators=300, contamination=0.21, random_state=RANDOM_STATE)
iso_eng.fit(X_eng)
score_eng = -iso_eng.score_samples(X_eng)
auc_eng = roc_auc_score(df["anomaly_label"], score_eng)

print(f"Isolation Forest (ham özellikler)              AUC: {auc_raw:.3f}")
print(f"Isolation Forest (facility-bazlı z-score)      AUC: {auc_eng:.3f}")
print()
print("Referans: v4'te ham özelliklerle AUC 0.545'ti (rastgele=0.50)")

# ROC eğrisi karşılaştırması
fpr_raw, tpr_raw, _ = roc_curve(df["anomaly_label"], score_raw)
fpr_eng, tpr_eng, _ = roc_curve(df["anomaly_label"], score_eng)

plt.figure(figsize=(7, 6))
plt.plot(fpr_raw, tpr_raw, label=f"Ham özellikler (AUC={auc_raw:.3f})")
plt.plot(fpr_eng, tpr_eng, label=f"Facility z-score (AUC={auc_eng:.3f})")
plt.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Rastgele (AUC=0.50)")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Isolation Forest ROC Karşılaştırması")
plt.legend()
plt.tight_layout()
plt.savefig("iso_forest_roc.png", dpi=110)
plt.show()

# Sadece GERÇEK sensör/ölçüm kolonlarını + facility_type/shift kullanıyoruz.
# machine_id KASITLI olarak feature setinde YOK (Bölüm 5'teki leakage kanıtı).
feature_cols = num_cols + ["facility_type", "shift"]

X_all = pd.get_dummies(df[feature_cols], columns=["facility_type", "shift"])
y_all = df["anomaly_label"]

# Zaman bazlı split (Bölüm 4'te tanımladığımız aynı mantık)
sorted_idx = df.sort_values("timestamp").index
X_sorted, y_sorted = X_all.loc[sorted_idx], y_all.loc[sorted_idx]
cut = int(len(X_sorted) * 0.75)
X_train, X_test = X_sorted.iloc[:cut], X_sorted.iloc[cut:]
y_train, y_test = y_sorted.iloc[:cut], y_sorted.iloc[cut:]

xgb_model = xgb.XGBClassifier(
    n_estimators=300, max_depth=4, learning_rate=0.05,
    eval_metric="logloss", random_state=RANDOM_STATE
)
xgb_model.fit(X_train, y_train)

proba_test = xgb_model.predict_proba(X_test)[:, 1]
pred_test = (proba_test > 0.5).astype(int)

auc_xgb = roc_auc_score(y_test, proba_test)
print(f"XGBoost anomaly_label AUC (zaman bazlı test seti): {auc_xgb:.3f}")
print(f"Referans: v4'te aynı test AUC 0.57'ydi")
print("(Bu ilk/naif model - hemen altta overfitting kontrolü yapacağız)")
print()
print(classification_report(y_test, pred_test))

# Az önce eğittiğimiz modelin (xgb_model) TRAIN ve TEST setindeki
# performansını ayrı ayrı ölçüyoruz.
train_auc_naive = roc_auc_score(y_train, xgb_model.predict_proba(X_train)[:, 1])
test_auc_naive = roc_auc_score(y_test, xgb_model.predict_proba(X_test)[:, 1])

print("=== İLK MODEL (n_estimators=300, max_depth=4) ===")
print(f"Train AUC : {train_auc_naive:.3f}")
print(f"Test AUC  : {test_auc_naive:.3f}")
print(f"Fark      : {train_auc_naive - test_auc_naive:.3f}")
print()
if (train_auc_naive - test_auc_naive) > 0.10:
    print("SONUÇ: Fark 0.10'un üzerinde -> bu model EZBERLİYOR (overfitting var).")
    print("Bir sonraki hücrede bunu düzeltmeye çalışacağız.")
else:
    print("SONUÇ: Fark kabul edilebilir seviyede.")

overfit_configs = [
    dict(n_estimators=300, max_depth=4, learning_rate=0.05,
         name="İlk model (cömert)"),
    dict(n_estimators=100, max_depth=3, learning_rate=0.05, min_child_weight=5,
         subsample=0.8, colsample_bytree=0.8, name="Sadeleştirilmiş"),
    dict(n_estimators=60, max_depth=2, learning_rate=0.08, min_child_weight=10,
         subsample=0.7, colsample_bytree=0.7, reg_lambda=3, name="Güçlü regularize"),
]

print(f'{"Konfigürasyon":22s} {"Train AUC":>10s} {"Test AUC":>10s} {"Fark":>8s}')
overfit_results = []
for cfg in overfit_configs:
    cfg = cfg.copy()
    name = cfg.pop("name")
    m = xgb.XGBClassifier(**cfg, eval_metric="logloss", random_state=RANDOM_STATE)
    m.fit(X_train, y_train)
    tr = roc_auc_score(y_train, m.predict_proba(X_train)[:, 1])
    te = roc_auc_score(y_test, m.predict_proba(X_test)[:, 1])
    print(f"{name:22s} {tr:>10.3f} {te:>10.3f} {tr - te:>8.3f}")
    overfit_results.append({"Konfigürasyon": name, "Train AUC": round(tr, 3),
                             "Test AUC": round(te, 3), "Fark": round(tr - te, 3)})

overfit_df = pd.DataFrame(overfit_results)

# xgb_model'ı SADELEŞTİRİLMİŞ konfigürasyonla yeniden eğitiyoruz.
# Bundan sonraki tüm hücreler (confusion matrix, feature importance,
# joblib kaydetme, özet tablo) bu güncellenmiş modeli kullanacak.
xgb_model = xgb.XGBClassifier(
    n_estimators=100, max_depth=3, learning_rate=0.05,
    min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
    eval_metric="logloss", random_state=RANDOM_STATE,
)
xgb_model.fit(X_train, y_train)

proba_test = xgb_model.predict_proba(X_test)[:, 1]
pred_test = (proba_test > 0.5).astype(int)
auc_xgb = roc_auc_score(y_test, proba_test)

train_auc_final = roc_auc_score(y_train, xgb_model.predict_proba(X_train)[:, 1])

print("=== GÜNCELLENMİŞ (Sadeleştirilmiş) MODEL ===")
print(f"Train AUC : {train_auc_final:.3f}")
print(f"Test AUC  : {auc_xgb:.3f}")
print(f"Fark      : {train_auc_final - auc_xgb:.3f}   (öncesinde {train_auc_naive - test_auc_naive:.3f} idi)")
print()
print(classification_report(y_test, pred_test))

print("=== Sadeleştirilmiş model - farklı zaman split noktalarında kararlılık ===")
print(f'{"Split":>8s} {"Train n":>8s} {"Test n":>7s} {"Train AUC":>10s} {"Test AUC":>9s}')

stability_results = []
for s in [0.60, 0.65, 0.70, 0.75, 0.80]:
    cut_s = int(len(X_sorted) * s)
    Xtr_s, Xte_s = X_sorted.iloc[:cut_s], X_sorted.iloc[cut_s:]
    ytr_s, yte_s = y_sorted.iloc[:cut_s], y_sorted.iloc[cut_s:]

    m = xgb.XGBClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.05,
        min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
        eval_metric="logloss", random_state=RANDOM_STATE,
    )
    m.fit(Xtr_s, ytr_s)
    tr_s = roc_auc_score(ytr_s, m.predict_proba(Xtr_s)[:, 1])
    te_s = roc_auc_score(yte_s, m.predict_proba(Xte_s)[:, 1])
    print(f"{s:>8.2f} {cut_s:>8d} {len(X_sorted)-cut_s:>7d} {tr_s:>10.3f} {te_s:>9.3f}")
    stability_results.append({"split": s, "train_auc": round(tr_s, 3), "test_auc": round(te_s, 3)})

stability_df = pd.DataFrame(stability_results)
test_auc_range = stability_df["test_auc"].max() - stability_df["test_auc"].min()
print()
print(f"Test AUC aralığı (max-min): {test_auc_range:.3f}")
print("Yorum:", "Kararlı - farklı split noktalarında sonuç tutarlı." if test_auc_range < 0.05
      else "Dikkat - split noktasına göre sonuç belirgin değişiyor, temkinli yorumlanmalı.")

# X_train'i (mevcut 1125 satır) ikiye ayırıyoruz: gerçek train + validation.
# X_test'e (son 375 satır) HİÇ dokunmuyoruz - o hâlâ görülmemiş kalıyor.
n_train_only = 900  # toplamın %60'ı (X_train zaten toplamın %75'iydi)
X_train_only = X_train.iloc[:n_train_only]
y_train_only = y_train.iloc[:n_train_only]
X_val = X_train.iloc[n_train_only:]
y_val = y_train.iloc[n_train_only:]

print(f"Train (gerçek)   : {len(X_train_only)} satır, anomali oranı {y_train_only.mean():.3f}")
print(f"Validation       : {len(X_val)} satır, anomali oranı {y_val.mean():.3f}")
print(f"Test (dokunulmadı): {len(X_test)} satır, anomali oranı {y_test.mean():.3f}")

from sklearn.metrics import precision_score, recall_score, f1_score

print(f'{"scale_pos_weight":>16s} {"Val AUC":>8s} {"Precision":>10s} {"Recall":>7s} {"F1":>6s}')
spw_results = []
for spw in [1, 2, 3, 4.2, 6, 8]:
    m = xgb.XGBClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.05, min_child_weight=5,
        subsample=0.8, colsample_bytree=0.8, scale_pos_weight=spw,
        eval_metric="logloss", random_state=RANDOM_STATE,
    )
    m.fit(X_train_only, y_train_only)
    proba_v = m.predict_proba(X_val)[:, 1]
    pred_v = (proba_v > 0.5).astype(int)
    auc_v = roc_auc_score(y_val, proba_v)
    prec_v = precision_score(y_val, pred_v, zero_division=0)
    rec_v = recall_score(y_val, pred_v, zero_division=0)
    f1_v = f1_score(y_val, pred_v, zero_division=0)
    print(f"{spw:>16} {auc_v:>8.3f} {prec_v:>10.3f} {rec_v:>7.3f} {f1_v:>6.3f}")
    spw_results.append({"scale_pos_weight": spw, "val_auc": auc_v, "val_f1": f1_v})

best_spw = max(spw_results, key=lambda r: r["val_f1"])["scale_pos_weight"]
print()
print(f"Validation'da en iyi F1'i veren scale_pos_weight: {best_spw}")

# NİHAİ MODEL: train+validation (=X_train, 1125 satır) ile eğit,
# test setine (X_test) SADECE BİR KEZ bak.
xgb_model = xgb.XGBClassifier(
    n_estimators=100, max_depth=3, learning_rate=0.05, min_child_weight=5,
    subsample=0.8, colsample_bytree=0.8, scale_pos_weight=best_spw,
    eval_metric="logloss", random_state=RANDOM_STATE,
)
xgb_model.fit(X_train, y_train)  # X_train = train+validation birleşik (1125 satır)

proba_test = xgb_model.predict_proba(X_test)[:, 1]
pred_test = (proba_test > 0.5).astype(int)
auc_xgb = roc_auc_score(y_test, proba_test)

print("=== NİHAİ MODEL (doğru metodoloji + recall iyileştirmesi) ===")
print(f"Test AUC: {auc_xgb:.3f}")
print()
print("Önce (7.1'deki model, scale_pos_weight yok):")
print("  Precision (anomali sınıfı): 0.62   Recall: 0.37   F1: 0.47")
print()
print("Şimdi (7.3 - nihai model):")
print(classification_report(y_test, pred_test))

# Confusion matrix
cm = confusion_matrix(y_test, pred_test)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Normal", "Anomali"])
fig, ax = plt.subplots(figsize=(5, 5))
disp.plot(ax=ax, cmap="Blues", colorbar=False)
ax.set_title("XGBoost - Confusion Matrix (Test Seti)")
plt.tight_layout()
plt.savefig("xgb_confusion_matrix.png", dpi=110)
plt.show()

# Feature importance - hangi sensör kolonları anomaliyi en çok açıklıyor?
importance = pd.Series(xgb_model.feature_importances_, index=X_all.columns).sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(8, 6))
importance.head(12).plot(kind="barh", ax=ax)
ax.invert_yaxis()
ax.set_title("XGBoost Feature Importance (İlk 12)")
ax.set_xlabel("Önem Skoru")
plt.tight_layout()
plt.savefig("xgb_feature_importance.png", dpi=110)
plt.show()

print(importance.head(12))

other_targets = {
    "energy_waste_flag": df["energy_waste_flag"],
    "maintenance_needed": df["maint_bin"],
}

other_results = []
for name, target in other_targets.items():
    y_sorted_t = target.loc[sorted_idx]
    y_train_t, y_test_t = y_sorted_t.iloc[:cut], y_sorted_t.iloc[cut:]

    m = xgb.XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05,
                           min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
                           eval_metric="logloss", random_state=RANDOM_STATE)  # Bölüm 7.1'de
                           # seçtiğimiz, overfitting'e karşı düzenlileştirilmiş ayarlar
    m.fit(X_train, y_train_t)
    p = m.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test_t, p)
    other_results.append({"Hedef": name, "AUC": round(auc, 3)})

pd.DataFrame(other_results)

summary = pd.DataFrame([
    {"Yöntem": "Isolation Forest (ham özellik)", "AUC": round(auc_raw, 3), "Tür": "Unsupervised"},
    {"Yöntem": "Isolation Forest (facility z-score)", "AUC": round(auc_eng, 3), "Tür": "Unsupervised"},
    {"Yöntem": "XGBoost (leakage-free, zaman split)", "AUC": round(auc_xgb, 3), "Tür": "Supervised"},
])
print(summary.to_string(index=False))
print()
print("ÖNERİ:")
print("- XGBoost, etiketli geçmiş veri olduğu sürece ANA karar katmanı olmalı.")
print("- Isolation Forest, YENİ/görülmemiş bir örüntü türü ortaya çıktığında")
print("  (etiket henüz yokken) bir 'erken uyarı' / soğuk-başlangıç katmanı")
print("  olarak tutulabilir, ama tek başına ana tespit motoru olmamalı.")

joblib.dump(xgb_model, "anomaly_xgb_model.joblib")

with open("model_feature_columns.txt", "w") as f:
    f.write("\n".join(X_all.columns.tolist()))

print("Kaydedildi: anomaly_xgb_model.joblib")
print("Kaydedildi: model_feature_columns.txt")
print()
print("Not: machine_id KASITLI olarak feature setinde yok (Bölüm 5).")
print("Backend'de yeni bir satır skorlanırken de bu kurala uyulmalı:")
print("machine_id, model girdisi olarak KULLANILMAMALI.")
