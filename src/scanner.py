import pandas as pd
import os

# -----------------------------
# Load CSV properly with split
# -----------------------------
def load_features(path):
    return pd.read_csv(path, engine="python")

# -----------------------------
# Score logic helpers
# -----------------------------
def confidence_score(level):
    levels = {"Unknown": 0, "Low": 1, "Medium": 2, "High": 3}
    return levels.get(str(level).strip(), 0) / 3

# -----------------------------
# Scoring weights
# -----------------------------
WEIGHTS = {
    "stale": 0.25,
    "owner": 0.20,
    "blocker": 0.15,
    "confidence": 0.20,
    "progress": 0.20
}

def compute_score(row):
    try:
        is_stale = (pd.to_datetime("2025-07-25") - pd.to_datetime(row["Updated"])).days > 14
    except:
        is_stale = True

    has_owner = str(row["PM_Owner"]).strip() not in ["", "nan"]
    has_blocker = str(row["Blockers"]).strip().lower() not in ["", "none", "no", "nan"]
    confidence = confidence_score(row["Confidence_Level"])
    try:
        progress = float(row["Progress_Percent"]) / 100
    except:
        progress = 0

    score = (
        WEIGHTS["stale"] * (0 if is_stale else 1) +
        WEIGHTS["owner"] * (1 if has_owner else 0) +
        WEIGHTS["blocker"] * (0 if has_blocker else 1) +
        WEIGHTS["confidence"] * confidence +
        WEIGHTS["progress"] * progress
    ) * 100

    return round(score, 2)

def score_to_label(score):
    if score >= 80:
        return "🟢 Green"
    elif score >= 60:
        return "🟡 Yellow"
    else:
        return "🔴 Red"

# -----------------------------
# Main runner
# -----------------------------
def run_scan():
    df = load_features(os.path.join("data","features.csv"))
    
    # Compute feature‐level health
    df["Health_Score"] = df.apply(compute_score, axis=1)
    df["Status_Label"] = df["Health_Score"].apply(score_to_label)

    # Feature report
    print("\n📊 Feature Health Report\n")
    print(df.to_string(index=False, 
                       columns=["Feature_ID","Title","Health_Score","Status_Label"],
                       formatters={"Health_Score":"{:.2f}".format}))

    # ——— OKR roll‐up ———
    okr_df = (
        df.groupby("OKR_ID")["Health_Score"]
          .mean()
          .reset_index(name="OKR_Health_Score")
    )
    okr_df["Status_Label"] = okr_df["OKR_Health_Score"].apply(score_to_label)

    print("\n🏆 OKR Health Report\n")
    print(okr_df.to_string(index=False, 
                            columns=["OKR_ID","OKR_Health_Score","Status_Label"],
                            formatters={"OKR_Health_Score":"{:.2f}".format}))


if __name__ == "__main__":
    run_scan()

