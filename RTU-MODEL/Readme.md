# RTU-MODEL — Edge + Fog Smart Solar PV Analytics

This directory implements core edge/fog algorithms for solar PV anomaly detection as part of the **LicheeRV + Pi fog** distributed monitoring system.

---

## Directory Structure

```
RTU-MODEL/
│
├── Notebooks and Scripts/
│     ├── yolo_pipeline_fixed.ipynb       # Full YOLOv8n train/export/benchmark workflow
│     └── logreg_leak_free-1.ipynb        # Leak-free logistic regression pipeline for fog risk scoring
│
├── model_output/
│     ├── LOG_REG/
│     │     └── model_config.json         # Logistic regression model performance/metadata
│     └── YOLO/
│           └── benchmark_report.txt      # YOLOv8n deployment + hardware benchmark results
│
├── runs/                                 # Experiment run outputs (YOLO, etc.)
│
├── training_dataset(imputed with synthetic img inferences).csv # Merged dataset: telemetry + (imputed) image features
│
├── requirements.txt                      # Python dependency list
│
└── Readme.md                             # THIS ReadMe
```

### Embedded Images/Screenshots

Below are some example images present in the directory (replace these with actual files for your case):

![YOLO ConfMatrix](model_output/YOLO/confusion_matrix.png)
*YOLOv8n confusion matrix (example)*

![ROC-AUC curve for logistic regression](model_output/LOG_REG/roc_curve.png)
*ROC-AUC curve for site-level logistic regression (example)*

---

## Key Components

### 1. [Notebooks and Scripts/](./Notebooks%20and%20Scripts/)
- **yolo_pipeline_fixed.ipynb**: End-to-end workflow for YOLOv8n:
    - Training on annotated PV panel anomalies (`bird_drop`, `cracked`, `dusty`, `panel`)
    - Export to ONNX INT8 for LicheeRV NPU acceleration
    - Hardware resource benchmarking
    - Extraction of final image-score features
- **logreg_leak_free-1.ipynb**: Implements:
    - Rigorous non-leaky telemetry feature selection
    - Cross-plant (site-to-site) generalization validation for anomaly/failure risk prediction
    - Benchmarking, thresholding, and config export for fog model

---

### 2. [model_output/LOG_REG/model_config.json](model_output/LOG_REG/model_config.json)
| Metric                | Value      |
|-----------------------|-----------|
| ROC-AUC (all data)    | 0.962     |
| Average Precision     | 0.950     |
| Brier Score           | 0.215     |
| Best F1 Threshold     | 0.05      |
| High Recall Threshold | 0.05      |
| Split Strategy        | cross_plant |
| Features Used         | PR, TEMP_DELTA, DC_AC_RATIO, PR_ROLL_MEAN, PR_ROLL_STD, TEMP_DELTA_SIGMA |
| Image Features        | Not used yet (planned)    |

*ROC curve example:*
![ROC and PR curves](model_output/LOG_REG/roc_pr_curves.png)

![feature_importance](model_output/LOG_REG/feature_importance.png)


---

### 3. [model_output/YOLO/benchmark_report.txt](model_output/YOLO/benchmark_report.txt)
| Metric               | Value     |
|----------------------|-----------|
| ONNX INT8 Model Size | 3.20 MB   |
| Mean CPU Latency     | 35.8 ms   |
| Est. NPU Latency     | 2.4 ms    |
| RAM Used             | 48.7 MB   |
| RAM Remaining        | 151.3 MB  |
| Memory Safe          | YES       |
| Viable for Deployment| YES       |

*Confusion matrix/mAP/etc. — see pipeline outputs for full metrics.*

---

### 4. [training_dataset(imputed with synthetic img inferences).csv](./training_dataset(imputed%20with%20synthetic%20img%20inferences).csv)
- Full dataset for model development: **telemetry** (sensor) + current **image scores**
- Ready for re-training as real YOLO on-device results are available

---

## Performance and System Suitability

- **YOLOv8n on LicheeRV (Linux SBC):**
    - <3.5 ms NPU inference
    - Fits in memory comfortably
    - No TinyML pipeline needed: full Python/ONNX support via Linux

- **Logistic Regression on Fog Node:**
    - Excellent discrimination (ROC-AUC >0.96)
    - Robust to site/operator variation (cross-plant validation)
    - Fully interpretable, recalibratable as new features/image scores arrive

---

## Frequently Asked Assignment/Design Questions

**Q: Why not TinyML?**  
*A: LicheeRV is a Linux SBC; YOLO runs in standard ONNX/Ultralytics Python. No resource constraints or firmware deployment; TinyML is only needed for microcontroller/MCU-class hardware.*

**Q: How does feature selection avoid leakage?**  
*A: Only non-leaky telemetry features (see model config) are included. Image scores will be included as soon as real YOLO outputs are fielded; synthetic features currently excluded.*

**Q: How are models evaluated?**  
*A: Cross-plant (site-to-site) splits, strict ROC-AUC, Average Precision, and calibration (Brier score) reporting. Hardware suitability is profiled in YOLO benchmark.*

**Q: Is deployment feasible on your edge/fog hardware?**  
*A: Yes! LicheeRV with NPU (YOLOv8n), and Python/scikit-learn-based regression on fog. Both pass runtime, memory, and accuracy requirements.*

---

## Outstanding/Remainder Documentation Questions

- **Integrate real YOLO on-device scores into main dataset.**  
  (Update logistic regression pipeline and reporting to use real, not synthetic, image features.)

- **Add per-class precision/recall tables and confusion matrices for YOLO.**

- **Field validation:**  
  As more real-world data is gathered, further validate thresholds/config.

- **Owner/Admin dashboard wiring:**  
  Add references for integration into the larger system if needed.

---

## Full Pipeline Reference

For in-depth details, see workflows and experiment results in [Notebooks and Scripts/](./Notebooks%20and%20Scripts/).

All model artifacts and configuration files are in [model_output/](./model_output/).

For more performance plots, open the directory images directly in your browser or markdown viewer.

---

## REPO

- https://github.com/Dev-onion73/SIH-RTU-Sim/RTU-MODEL

