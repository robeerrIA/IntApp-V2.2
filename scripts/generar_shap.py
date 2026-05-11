"""Genera todas las figuras SHAP para el TFM."""
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
import shap
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

DIR_MODELOS = RAIZ / "modelos"
DIR_DATOS   = RAIZ / "datos" / "procesados"
DIR_FIGS    = RAIZ / "figuras"
DIR_FIGS.mkdir(parents=True, exist_ok=True)

SEMILLA = 42
COLUMNA = "riesgo_lesion"

# ── Datos (CSV ya preprocesado y escalado) ────────────────────────────────────
df = pd.read_csv(DIR_DATOS / "procesado_dataset_sintetico.csv")
df = df[df[COLUMNA] != "no_concluyente"].reset_index(drop=True)

X = df.drop(columns=[COLUMNA])
y = df[COLUMNA]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=SEMILLA, stratify=y
)
print(f"Train: {len(X_train)} | Test: {len(X_test)}")

# ── Modelo ───────────────────────────────────────────────────────────────────
modelo = joblib.load(DIR_MODELOS / "mejor_modelo.pkl")
print(f"Modelo: {type(modelo).__name__}")
print(f"Clases: {modelo.classes_}")

clases     = list(modelo.classes_)
idx_alto   = clases.index("alto")
print(f"idx_alto = {idx_alto}  ({clases})")

# ── KernelExplainer ───────────────────────────────────────────────────────────
# TreeExplainer no soporta GradientBoostingClassifier multiclase (SHAP 0.51).
print("Calculando background (kmeans k=50)...")
background = shap.kmeans(X_train, 50)

print("Creando KernelExplainer...")
explainer = shap.KernelExplainer(modelo.predict_proba, background)

print("Calculando SHAP values (nsamples=200, puede tardar ~3 min)...")
shap_raw = explainer.shap_values(X_test, nsamples=200)
# SHAP 0.51: shape = (n_samples, n_features, n_classes) como ndarray
# versiones antiguas: lista de (n_samples, n_features), una por clase
if isinstance(shap_raw, np.ndarray) and shap_raw.ndim == 3:
    # shape (n_samples, n_features, n_classes)
    shap_3d = shap_raw
    ev_array = np.array(explainer.expected_value)
    shap_alto = shap_3d[:, :, idx_alto]          # (n_samples, n_features)
    ev_alto   = float(ev_array[idx_alto])
    print(f"ndarray 3D: {shap_3d.shape} → shap_alto: {shap_alto.shape}")
elif isinstance(shap_raw, list):
    shap_alto = np.array(shap_raw[idx_alto])     # (n_samples, n_features)
    ev_alto   = float(np.array(explainer.expected_value)[idx_alto])
    print(f"list {len(shap_raw)} clases → shap_alto: {shap_alto.shape}")
else:
    shap_alto = np.array(shap_raw)
    ev_alto   = float(explainer.expected_value)
    print(f"shape: {shap_alto.shape}")

# ── Importancia media ────────────────────────────────────────────────────────
importancia = pd.DataFrame({
    "variable":     X_test.columns,
    "shap_mean_abs": np.abs(shap_alto).mean(axis=0),
}).sort_values("shap_mean_abs", ascending=False).reset_index(drop=True)
print("\nTop 10 variables (SHAP clase 'alto'):")
print(importancia.head(10).to_string(index=False))

# ── Figura 1: barras ─────────────────────────────────────────────────────────
plt.figure(figsize=(10, 8))
shap.summary_plot(shap_alto, X_test, plot_type="bar", show=False, max_display=20)
plt.title("Importancia global de variables (SHAP — clase 'alto')", fontsize=14, fontweight="bold")
plt.xlabel("Valor SHAP medio absoluto")
plt.tight_layout()
plt.savefig(DIR_FIGS / "shap_importancia_global.png", dpi=150, bbox_inches="tight")
plt.close()
print("Guardada: shap_importancia_global.png")

# ── Figura 2: beeswarm ───────────────────────────────────────────────────────
plt.figure(figsize=(10, 9))
shap.summary_plot(shap_alto, X_test, show=False, max_display=20)
plt.title("Efecto de cada variable sobre la predicción (clase 'alto')", fontsize=14, fontweight="bold")
plt.xlabel("Valor SHAP")
plt.tight_layout()
plt.savefig(DIR_FIGS / "shap_beeswarm.png", dpi=150, bbox_inches="tight")
plt.close()
print("Guardada: shap_beeswarm.png")

# ── Figuras 3-5: waterfall por clase ─────────────────────────────────────────
def guardar_waterfall(clase_nombre: str) -> None:
    indices = np.where(y_test.values == clase_nombre)[0]
    if len(indices) == 0:
        print(f"Sin casos '{clase_nombre}' en test")
        return
    sv_clase  = shap_alto[indices]
    centroide = sv_clase.mean(axis=0)
    idx       = indices[np.argmin(np.linalg.norm(sv_clase - centroide, axis=1))]

    exp = shap.Explanation(
        values=shap_alto[idx],
        base_values=ev_alto,
        data=X_test.iloc[idx].values,
        feature_names=list(X_test.columns),
    )
    plt.figure(figsize=(10, 7))
    shap.plots.waterfall(exp, max_display=15, show=False)
    plt.title(f"Explicación individual — Riesgo {clase_nombre.upper()}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(DIR_FIGS / f"shap_caso_{clase_nombre}.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Guardada: shap_caso_{clase_nombre}.png")

for c in ["bajo", "medio", "alto"]:
    guardar_waterfall(c)

# ── Figuras 6-8: dependencia top 3 ───────────────────────────────────────────
top3 = importancia["variable"].head(3).tolist()
print(f"\nTop 3 para dependencia: {top3}")
for var in top3:
    fig, ax = plt.subplots(figsize=(9, 6))
    shap.dependence_plot(var, shap_alto, X_test, ax=ax, show=False)
    ax.set_xlabel(var, fontsize=11)
    ax.set_ylabel("Valor SHAP (impacto en predicción — clase 'alto')", fontsize=11)
    ax.set_title(f"Dependencia SHAP — {var}", fontsize=12, fontweight="bold")
    plt.tight_layout()
    nombre = f"shap_dependencia_{var.replace('/', '_')}.png"
    plt.savefig(DIR_FIGS / nombre, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Guardada: {nombre}")

# ── Resumen ───────────────────────────────────────────────────────────────────
print("\n=== Figuras SHAP generadas ===")
for f in sorted(DIR_FIGS.glob("shap_*.png")):
    print(f"  {f.name:55s}  {f.stat().st_size/1024:.1f} KB")
