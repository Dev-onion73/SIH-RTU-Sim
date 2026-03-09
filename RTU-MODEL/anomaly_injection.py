"""
=============================================================
Synthetic Anomaly Injection & Pseudo-Label Generation
Solar PV Monitoring System — RTU Logistic Regression Training
=============================================================

WHAT THIS SCRIPT DOES:
  1. Loads Plant1 and Plant2 telemetry + weather CSVs
  2. Merges and computes derived features (PR, TEMP_DELTA, etc.)
  3. Establishes per-inverter baseline from real data
  4. Injects physics-grounded synthetic anomalies into normal rows
  5. Assigns pseudo-labels to every row (normal / dusty / bird_drop / cracked)
  6. Assigns synthetic image scores consistent with each label
  7. Outputs a balanced, training-ready CSV

HOW TO USE:
  Step 1 — Place your four CSV files in the same directory as this script:
            Plant1_filtered.csv
            Plant1_Weather_filtered.csv
            Plant2_filtered.csv
            Plant2_Weather_filtered.csv

  Step 2 — Run:
            python anomaly_injection.py

  Step 3 — Output file produced:
            training_dataset.csv

  Step 4 — Feed training_dataset.csv to your logistic regression trainer.
            Target column:  'label'       (0=normal, 1=anomaly)
            Fault column:   'fault_type'  (normal/dusty/bird_drop/cracked)
            Feature columns listed at bottom of this file.

DEPENDENCIES:
  pip install pandas numpy scikit-learn
"""

import pandas as pd
import numpy as np
from sklearn.utils import resample

# ─────────────────────────────────────────────
# CONFIGURATION — adjust thresholds here
# derived empirically from EDA on Jethani dataset
# ─────────────────────────────────────────────
CFG = {
    # Irradiance floor — below this is night/twilight, exclude
    "irradiation_floor": 0.01,

    # Merge tolerance between generation and weather timestamps
    "merge_tolerance_min": 15,

    # Rolling window size (8 × 15min = 2 hours)
    "rolling_window": 8,
    "rolling_min_periods": 3,

    # ── Normal envelope ──────────────────────
    # PR deviation from inverter baseline below which row is normal
    "normal_pr_dev_max": 0.10,

    # ── Dusty thresholds ────────────────────
    # Gradual PR drop: 10–25% below baseline
    "dusty_pr_dev_min": 0.10,
    "dusty_pr_dev_max": 0.25,
    # Slope must be consistently negative (gradual decline)
    "dusty_slope_threshold": -5.0,
    # Temp delta must be within normal range
    "dusty_temp_dev_max_sigma": 1.5,

    # ── Bird drop thresholds ─────────────────
    # Sudden PR drop: > 15% within short window
    "bird_pr_dev_min": 0.15,
    # Sharp slope indicating sudden drop within ~2hr window
    "bird_slope_threshold": -20.0,
    "bird_temp_dev_max_sigma": 1.5,

    # ── Cracked thresholds ───────────────────
    # Severe persistent drop: > 25%
    "crack_pr_dev_min": 0.25,
    # High rolling std indicates erratic behaviour
    "crack_roll_std_min_sigma": 1.0,
    # Elevated temp delta (thermal stress from hotspot)
    "crack_temp_dev_min_sigma": 1.5,

    # ── Synthetic injection parameters ───────
    # Target fraction of anomaly rows per class in final dataset
    # Total anomaly target ~40%, split across 3 classes
    "target_dusty_fraction":     0.15,
    "target_bird_drop_fraction": 0.13,
    "target_cracked_fraction":   0.12,

    # Noise std added during injection (as fraction of feature value)
    "injection_noise_std": 0.03,

    # Random seed for reproducibility
    "random_seed": 42,
}

# ─────────────────────────────────────────────
# SYNTHETIC IMAGE SCORE PARAMETERS
# Each fault class gets a score distribution
# for each image class (panel, dusty, cracked, bird_drop)
# format: (mean, std) — clipped to [0,1]
# ─────────────────────────────────────────────
IMAGE_SCORE_PARAMS = {
    #              panel       dusty       cracked     bird_drop
    "normal":   [(0.85,0.05), (0.06,0.03), (0.04,0.02), (0.05,0.03)],
    "dusty":    [(0.08,0.04), (0.78,0.07), (0.06,0.03), (0.08,0.04)],
    "bird_drop":[(0.07,0.03), (0.09,0.04), (0.05,0.02), (0.79,0.07)],
    "cracked":  [(0.06,0.03), (0.07,0.03), (0.80,0.07), (0.07,0.03)],
}


# ═════════════════════════════════════════════
# STEP 1 — LOAD AND MERGE DATA
# ═════════════════════════════════════════════
def load_and_merge(gen_path, wea_path, dayfirst=False):
    """
    Load generation and weather CSVs, merge on timestamp.
    Returns merged daytime-only DataFrame.
    """
    gen = pd.read_csv(gen_path)
    wea = pd.read_csv(wea_path)

    gen['DATE_TIME'] = pd.to_datetime(gen['DATE_TIME'], dayfirst=dayfirst)
    wea['DATE_TIME'] = pd.to_datetime(wea['DATE_TIME'])

    # Weather has one sensor — aggregate to timestamp level
    wea_agg = wea.groupby('DATE_TIME')[
        ['AMBIENT_TEMPERATURE', 'MODULE_TEMPERATURE', 'IRRADIATION']
    ].mean().reset_index()

    # Merge generation with weather using nearest timestamp within tolerance
    merged = pd.merge_asof(
        gen.sort_values('DATE_TIME'),
        wea_agg.sort_values('DATE_TIME'),
        on='DATE_TIME',
        tolerance=pd.Timedelta(f"{CFG['merge_tolerance_min']}min")
    )

    # Drop night readings
    merged = merged[merged['IRRADIATION'] > CFG['irradiation_floor']].copy()
    merged.dropna(subset=['AMBIENT_TEMPERATURE', 'MODULE_TEMPERATURE'], inplace=True)
    return merged


# ═════════════════════════════════════════════
# STEP 2 — FEATURE ENGINEERING
# ═════════════════════════════════════════════
def engineer_features(df):
    """
    Compute PR, TEMP_DELTA, DC_AC_RATIO, rolling stats,
    and per-inverter baseline deviation.
    """
    df = df.copy()
    df = df.sort_values(['SOURCE_KEY', 'DATE_TIME'])

    # Core features
    df['PR']          = df['AC_POWER'] / df['IRRADIATION']
    df['TEMP_DELTA']  = df['MODULE_TEMPERATURE'] - df['AMBIENT_TEMPERATURE']
    df['DC_AC_RATIO'] = df['DC_POWER'] / df['AC_POWER']

    w = CFG['rolling_window']
    mp = CFG['rolling_min_periods']

    # Rolling statistics per inverter
    grp = df.groupby('SOURCE_KEY')['PR']
    df['PR_ROLL_MEAN'] = grp.transform(lambda x: x.rolling(w, min_periods=mp).mean())
    df['PR_ROLL_STD']  = grp.transform(lambda x: x.rolling(w, min_periods=mp).std())
    df['PR_SLOPE']     = grp.transform(
        lambda x: x.rolling(w, min_periods=mp).apply(
            lambda y: np.polyfit(range(len(y)), y, 1)[0] if len(y) >= mp else np.nan,
            raw=True
        )
    )

    # Per-inverter baseline (mean and std of PR across all its readings)
    baseline = df.groupby('SOURCE_KEY')['PR'].agg(
        PR_BASE_MEAN='mean', PR_BASE_STD='std'
    ).reset_index()
    df = df.merge(baseline, on='SOURCE_KEY', how='left')

    # Normalised PR deviation from inverter's own baseline
    # Positive value = performing BELOW baseline (degradation)
    df['PR_DEV'] = (df['PR_BASE_MEAN'] - df['PR']) / df['PR_BASE_MEAN']

    # Temp delta deviation in sigma units from plant-wide mean
    td_mean = df['TEMP_DELTA'].mean()
    td_std  = df['TEMP_DELTA'].std()
    df['TEMP_DELTA_SIGMA'] = (df['TEMP_DELTA'] - td_mean) / td_std

    df.dropna(subset=['PR_ROLL_MEAN', 'PR_ROLL_STD', 'PR_SLOPE'], inplace=True)
    return df


# ═════════════════════════════════════════════
# STEP 3 — PSEUDO-LABEL ASSIGNMENT
# ═════════════════════════════════════════════
def assign_pseudo_labels(df):
    """
    Apply heuristic rules to assign fault_type and binary label.

    Rule priority (first match wins):
      1. cracked   — severe persistent PR drop + thermal stress + erratic
      2. bird_drop — sudden sharp PR drop within short window
      3. dusty     — gradual negative PR slope + moderate PR drop
      4. normal    — everything else
    """
    df = df.copy()
    df['fault_type'] = 'normal'
    df['label'] = 0

    roll_std_threshold = df['PR_ROLL_STD'].mean() + \
        CFG['crack_roll_std_min_sigma'] * df['PR_ROLL_STD'].std()

    # ── Cracked ──────────────────────────────
    crack_mask = (
        (df['PR_DEV']          >  CFG['crack_pr_dev_min']) &
        (df['PR_ROLL_STD']     >  roll_std_threshold) &
        (df['TEMP_DELTA_SIGMA'] > CFG['crack_temp_dev_min_sigma'])
    )
    df.loc[crack_mask, 'fault_type'] = 'cracked'
    df.loc[crack_mask, 'label'] = 1

    # ── Bird Drop ─────────────────────────────
    bird_mask = (
        (df['fault_type'] == 'normal') &
        (df['PR_DEV']     >  CFG['bird_pr_dev_min']) &
        (df['PR_SLOPE']   <  CFG['bird_slope_threshold']) &
        (df['TEMP_DELTA_SIGMA'] < CFG['bird_temp_dev_max_sigma'])
    )
    df.loc[bird_mask, 'fault_type'] = 'bird_drop'
    df.loc[bird_mask, 'label'] = 1

    # ── Dusty ────────────────────────────────
    dusty_mask = (
        (df['fault_type'] == 'normal') &
        (df['PR_DEV']     >  CFG['dusty_pr_dev_min']) &
        (df['PR_DEV']     <= CFG['dusty_pr_dev_max']) &
        (df['PR_SLOPE']   <  CFG['dusty_slope_threshold']) &
        (df['TEMP_DELTA_SIGMA'] < CFG['dusty_temp_dev_max_sigma'])
    )
    df.loc[dusty_mask, 'fault_type'] = 'dusty'
    df.loc[dusty_mask, 'label'] = 1

    return df


# ═════════════════════════════════════════════
# STEP 4 — SYNTHETIC ANOMALY INJECTION
# ═════════════════════════════════════════════
def inject_synthetic_anomalies(df, target_n_dusty, target_n_bird, target_n_crack):
    """
    Takes normal rows and injects physics-grounded perturbations
    to create additional synthetic anomaly samples.

    Each anomaly type perturbs features according to its
    physical failure mechanism.
    """
    rng = np.random.default_rng(CFG['random_seed'])
    normal_rows = df[df['fault_type'] == 'normal'].copy()
    synthetic_frames = []

    def add_noise(series, std_frac=CFG['injection_noise_std']):
        noise = rng.normal(0, std_frac * series.abs().mean(), size=len(series))
        return series + noise

    # ── Synthetic Dusty ──────────────────────
    # Physical mechanism: dust accumulation uniformly reduces
    # current (and thus power) while voltage stays stable.
    # PR drops gradually — simulate as moderate uniform PR reduction.
    n_existing_dusty = (df['fault_type'] == 'dusty').sum()
    n_inject_dusty = max(0, target_n_dusty - n_existing_dusty)

    if n_inject_dusty > 0:
        sample = normal_rows.sample(n=n_inject_dusty, replace=True,
                                    random_state=CFG['random_seed'])
        # Reduce AC_POWER by 15–25% (uniform soiling effect)
        reduction = rng.uniform(0.15, 0.25, size=len(sample))
        sample['AC_POWER']  = sample['AC_POWER'] * (1 - reduction)
        sample['AC_POWER']  = add_noise(sample['AC_POWER'])
        # DC_POWER follows proportionally (current drop)
        sample['DC_POWER']  = sample['DC_POWER'] * (1 - reduction * 0.9)
        # Recompute derived features
        sample['PR']        = sample['AC_POWER'] / sample['IRRADIATION']
        sample['PR_DEV']    = (sample['PR_BASE_MEAN'] - sample['PR']) / sample['PR_BASE_MEAN']
        sample['PR_SLOPE']  = rng.uniform(-15, -5, size=len(sample))
        sample['fault_type'] = 'dusty'
        sample['label']     = 1
        sample['synthetic'] = True
        synthetic_frames.append(sample)

    # ── Synthetic Bird Drop ───────────────────
    # Physical mechanism: localised obstruction causes
    # sudden sharp current drop in affected string.
    # PR drops sharply within one reporting window.
    n_existing_bird = (df['fault_type'] == 'bird_drop').sum()
    n_inject_bird = max(0, target_n_bird - n_existing_bird)

    if n_inject_bird > 0:
        sample = normal_rows.sample(n=n_inject_bird, replace=True,
                                    random_state=CFG['random_seed'] + 1)
        reduction = rng.uniform(0.18, 0.35, size=len(sample))
        sample['AC_POWER']  = sample['AC_POWER'] * (1 - reduction)
        sample['AC_POWER']  = add_noise(sample['AC_POWER'])
        sample['DC_POWER']  = sample['DC_POWER'] * (1 - reduction * 0.85)
        sample['PR']        = sample['AC_POWER'] / sample['IRRADIATION']
        sample['PR_DEV']    = (sample['PR_BASE_MEAN'] - sample['PR']) / sample['PR_BASE_MEAN']
        # Sharp sudden slope — distinguishes from dusty
        sample['PR_SLOPE']  = rng.uniform(-60, -20, size=len(sample))
        sample['fault_type'] = 'bird_drop'
        sample['label']     = 1
        sample['synthetic'] = True
        synthetic_frames.append(sample)

    # ── Synthetic Cracked ────────────────────
    # Physical mechanism: crack increases series resistance,
    # causing voltage sag under load and localised heating.
    # PR drops severely and erratically.
    # Module temperature elevates above normal.
    n_existing_crack = (df['fault_type'] == 'cracked').sum()
    n_inject_crack = max(0, target_n_crack - n_existing_crack)

    if n_inject_crack > 0:
        sample = normal_rows.sample(n=n_inject_crack, replace=True,
                                    random_state=CFG['random_seed'] + 2)
        reduction = rng.uniform(0.25, 0.45, size=len(sample))
        sample['AC_POWER']   = sample['AC_POWER'] * (1 - reduction)
        # Add extra noise to simulate erratic behaviour
        erratic_noise = rng.normal(0, 0.08 * sample['AC_POWER'].abs().mean(),
                                   size=len(sample))
        sample['AC_POWER']   = sample['AC_POWER'] + erratic_noise
        sample['DC_POWER']   = sample['DC_POWER'] * (1 - reduction * 0.95)
        # Voltage specifically sags (crack increases series resistance)
        sample['PR']         = sample['AC_POWER'] / sample['IRRADIATION']
        sample['PR_DEV']     = (sample['PR_BASE_MEAN'] - sample['PR']) / sample['PR_BASE_MEAN']
        sample['PR_ROLL_STD'] = sample['PR_ROLL_STD'] * rng.uniform(2.0, 3.5, size=len(sample))
        # Thermal stress — module temperature elevated
        sample['MODULE_TEMPERATURE'] = sample['MODULE_TEMPERATURE'] + \
                                       rng.uniform(8, 18, size=len(sample))
        sample['TEMP_DELTA'] = sample['MODULE_TEMPERATURE'] - sample['AMBIENT_TEMPERATURE']
        td_mean = df['TEMP_DELTA'].mean()
        td_std  = df['TEMP_DELTA'].std()
        sample['TEMP_DELTA_SIGMA'] = (sample['TEMP_DELTA'] - td_mean) / td_std
        sample['fault_type'] = 'cracked'
        sample['label']      = 1
        sample['synthetic']  = True
        synthetic_frames.append(sample)

    if synthetic_frames:
        df['synthetic'] = False
        df = pd.concat([df] + synthetic_frames, ignore_index=True)

    return df


# ═════════════════════════════════════════════
# STEP 5 — SYNTHETIC IMAGE SCORE GENERATION
# ═════════════════════════════════════════════
def generate_image_scores(df):
    """
    For each row assign synthetic image classifier scores
    consistent with the fault_type label.

    Scores are sampled from Gaussian distributions
    and normalised to sum to 1.0 (simulating softmax output).
    """
    rng = np.random.default_rng(CFG['random_seed'] + 99)
    n = len(df)

    panel_scores    = np.zeros(n)
    dusty_scores    = np.zeros(n)
    cracked_scores  = np.zeros(n)
    bird_scores     = np.zeros(n)

    for fault_type, params in IMAGE_SCORE_PARAMS.items():
        mask = df['fault_type'] == fault_type
        count = mask.sum()
        if count == 0:
            continue

        raw = np.column_stack([
            np.clip(rng.normal(p[0], p[1], count), 0, 1)
            for p in params
        ])
        # Normalise rows to sum to 1
        raw = raw / raw.sum(axis=1, keepdims=True)

        idx = np.where(mask)[0]
        panel_scores[idx]   = raw[:, 0]
        dusty_scores[idx]   = raw[:, 1]
        cracked_scores[idx] = raw[:, 2]
        bird_scores[idx]    = raw[:, 3]

    df['img_panel_score']    = panel_scores
    df['img_dusty_score']    = dusty_scores
    df['img_cracked_score']  = cracked_scores
    df['img_bird_drop_score'] = bird_scores

    return df


# ═════════════════════════════════════════════
# STEP 6 — BALANCE DATASET
# ═════════════════════════════════════════════
def balance_dataset(df):
    """
    Oversample minority anomaly classes to reach target fractions.
    Does NOT downsample normal class — keeps all real normal data.
    """
    total = len(df)
    target_dusty = int(total * CFG['target_dusty_fraction'])
    target_bird  = int(total * CFG['target_bird_drop_fraction'])
    target_crack = int(total * CFG['target_cracked_fraction'])

    df = inject_synthetic_anomalies(df, target_dusty, target_bird, target_crack)
    return df


# ═════════════════════════════════════════════
# MAIN PIPELINE
# ═════════════════════════════════════════════
def run_pipeline():
    print("=" * 60)
    print("Solar PV Anomaly Injection Pipeline")
    print("=" * 60)

    # Load Plant 1 (dayfirst=True for DD-MM-YYYY format)
    print("\n[1/6] Loading Plant 1...")
    p1 = load_and_merge(
        'Plant1_filtered.csv',
        'Plant1_Weather_filtered.csv',
        dayfirst=True
    )
    p1['PLANT_ID'] = 1
    print(f"      Plant1 daytime rows: {len(p1)}")

    # Load Plant 2
    print("[1/6] Loading Plant 2...")
    p2 = load_and_merge(
        'Plant2_filtered.csv',
        'Plant2_Weather_filtered.csv',
        dayfirst=False
    )
    p2['PLANT_ID'] = 2
    print(f"      Plant2 daytime rows: {len(p2)}")

    # Combine
    df = pd.concat([p1, p2], ignore_index=True)
    print(f"      Combined total rows: {len(df)}")

    # Feature engineering
    print("\n[2/6] Engineering features...")
    df = engineer_features(df)
    print(f"      Rows after rolling stats: {len(df)}")

    # Pseudo-label assignment
    print("\n[3/6] Assigning pseudo-labels from heuristics...")
    df = assign_pseudo_labels(df)
    counts = df['fault_type'].value_counts()
    print(f"      Label distribution (real data):")
    for ft, cnt in counts.items():
        print(f"        {ft:12s}: {cnt:6d}  ({cnt/len(df)*100:.1f}%)")

    # Balance via synthetic injection
    print("\n[4/6] Injecting synthetic anomalies to balance classes...")
    df['synthetic'] = False
    total = len(df)
    target_dusty = int(total * CFG['target_dusty_fraction'])
    target_bird  = int(total * CFG['target_bird_drop_fraction'])
    target_crack = int(total * CFG['target_cracked_fraction'])
    df = inject_synthetic_anomalies(df, target_dusty, target_bird, target_crack)
    counts2 = df['fault_type'].value_counts()
    print(f"      Label distribution (after injection):")
    for ft, cnt in counts2.items():
        print(f"        {ft:12s}: {cnt:6d}  ({cnt/len(df)*100:.1f}%)")
    print(f"      Synthetic rows added: {df['synthetic'].sum()}")

    # Generate image scores
    print("\n[5/6] Generating synthetic image scores...")
    df = generate_image_scores(df)
    print("      Image scores assigned.")

    # Select and export training columns
    print("\n[6/6] Exporting training dataset...")
    FEATURE_COLS = [
        'PLANT_ID',
        'SOURCE_KEY',
        'DATE_TIME',
        # Raw telemetry
        'DC_POWER',
        'AC_POWER',
        'AMBIENT_TEMPERATURE',
        'MODULE_TEMPERATURE',
        'IRRADIATION',
        # Derived features
        'PR',
        'TEMP_DELTA',
        'DC_AC_RATIO',
        # Rolling features
        'PR_ROLL_MEAN',
        'PR_ROLL_STD',
        'PR_SLOPE',
        'PR_DEV',
        'TEMP_DELTA_SIGMA',
        # Synthetic image scores
        'img_panel_score',
        'img_dusty_score',
        'img_cracked_score',
        'img_bird_drop_score',
        # Labels
        'fault_type',
        'label',
        'synthetic',
    ]

    output = df[FEATURE_COLS].copy()
    output.to_csv('training_dataset.csv', index=False)

    print(f"\n{'='*60}")
    print(f"DONE. Output: training_dataset.csv")
    print(f"Total rows:   {len(output)}")
    print(f"Features:     {len(FEATURE_COLS) - 3} (excl. ID/label cols)")
    print(f"\nLOGISTIC REGRESSION INPUT FEATURES:")
    model_features = [
        'PR', 'TEMP_DELTA', 'DC_AC_RATIO',
        'PR_ROLL_MEAN', 'PR_ROLL_STD', 'PR_SLOPE', 'PR_DEV',
        'TEMP_DELTA_SIGMA',
        'img_panel_score', 'img_dusty_score',
        'img_cracked_score', 'img_bird_drop_score'
    ]
    for f in model_features:
        print(f"  - {f}")
    print(f"\nTARGET COLUMN:  label  (0=normal, 1=anomaly)")
    print(f"FAULT COLUMN:   fault_type  (for analysis only, not model input)")
    print(f"{'='*60}")


if __name__ == '__main__':
    run_pipeline()
