import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def get_hyp_band_columns(df: pd.DataFrame):
    hyp_bands = []
    for col in df.columns:
        try:
            int(col)
            hyp_bands.append(col)
        except ValueError:
            continue
    band_wavelengths = [int(b) for b in hyp_bands]
    return hyp_bands, band_wavelengths


def eda_q1_soil_moisture(df: pd.DataFrame, out_dir: str):
    sm = df["soil_moisture"].astype(float)

    mean_sm = sm.mean()
    median_sm = sm.median()
    std_sm = sm.std()
    skew_sm = sm.skew()
    kurt_sm = sm.kurtosis()

    q1 = sm.quantile(0.25)
    q3 = sm.quantile(0.75)
    iqr = q3 - q1
    fence_lo = q1 - 1.5 * iqr
    fence_hi = q3 + 1.5 * iqr
    outliers = sm[(sm < fence_lo) | (sm > fence_hi)]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].hist(sm, bins=25, color="steelblue", edgecolor="white", linewidth=0.6)
    axes[0].axvline(mean_sm, color="red", linestyle="--", linewidth=1.5, label=f"Mean: {mean_sm:.2f}%")
    axes[0].axvline(median_sm, color="orange", linestyle="-", linewidth=1.5, label=f"Median: {median_sm:.2f}%")
    axes[0].set_xlabel("Soil Moisture (%)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Distribution of Soil Moisture")
    axes[0].legend(fontsize=9)

    axes[1].boxplot(
        sm,
        vert=True,
        patch_artist=True,
        boxprops=dict(facecolor="steelblue", color="navy"),
        medianprops=dict(color="red", linewidth=2),
        flierprops=dict(marker="o", color="red", markersize=6),
    )
    axes[1].set_ylabel("Soil Moisture (%)")
    axes[1].set_title("Boxplot of Soil Moisture")
    axes[1].set_xticks([1])
    axes[1].set_xticklabels(["soil_moisture"])

    plt.tight_layout()
    out_path = os.path.join(out_dir, "eda_q1_soil_moisture_dist.png")
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "Mean (%)": round(mean_sm, 4),
        "Median (%)": round(median_sm, 4),
        "Std Dev (%)": round(std_sm, 4),
        "Skewness": round(skew_sm, 4),
        "Excess Kurtosis": round(kurt_sm, 4),
        "IQR (%)": round(iqr, 4),
        "Lower Fence (%)": round(fence_lo, 4),
        "Upper Fence (%)": round(fence_hi, 4),
        "Outlier Count": int(len(outliers)),
    }
    return summary


def eda_q2_correlations(df: pd.DataFrame, hyp_bands: list[str], band_wavelengths: list[int], out_dir: str, top_k: int = 5):
    corr_sm = df[hyp_bands].corrwith(df["soil_moisture"])
    corr_st = df[hyp_bands].corrwith(df["soil_temperature"])

    top5_sm = corr_sm.abs().nlargest(top_k)
    top5_st = corr_st.abs().nlargest(top_k)

    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)

    axes[0].plot(band_wavelengths, corr_sm.values, color="steelblue", linewidth=1.5)
    axes[0].axhline(0, color="black", linewidth=0.8, linestyle="--")
    axes[0].fill_between(
        band_wavelengths,
        corr_sm.values,
        0,
        where=[v > 0 for v in corr_sm.values],
        alpha=0.2,
        color="steelblue",
    )
    axes[0].fill_between(
        band_wavelengths,
        corr_sm.values,
        0,
        where=[v < 0 for v in corr_sm.values],
        alpha=0.2,
        color="tomato",
    )
    axes[0].set_ylabel("Pearson r")
    axes[0].set_title("Correlation of Hyperspectral Bands with Soil Moisture")
    axes[0].set_ylim(-1, 1)
    axes[0].yaxis.set_major_locator(ticker.MultipleLocator(0.2))

    axes[1].plot(band_wavelengths, corr_st.values, color="darkorange", linewidth=1.5)
    axes[1].axhline(0, color="black", linewidth=0.8, linestyle="--")
    axes[1].fill_between(
        band_wavelengths,
        corr_st.values,
        0,
        where=[v > 0 for v in corr_st.values],
        alpha=0.2,
        color="darkorange",
    )
    axes[1].fill_between(
        band_wavelengths,
        corr_st.values,
        0,
        where=[v < 0 for v in corr_st.values],
        alpha=0.2,
        color="purple",
    )
    axes[1].set_ylabel("Pearson r")
    axes[1].set_xlabel("Wavelength (nm)")
    axes[1].set_title("Correlation of Hyperspectral Bands with Soil Temperature")
    axes[1].set_ylim(-1, 1)
    axes[1].yaxis.set_major_locator(ticker.MultipleLocator(0.2))

    plt.tight_layout()
    out_path = os.path.join(out_dir, "eda_q2_band_correlations.png")
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    def format_top(series):
        items = []
        for band in series.index:
            items.append((int(band), float(corr_sm[band]) if series is top5_sm else float(corr_st[band])))
        return items

    top_sm = [(int(b), float(corr_sm[b])) for b in top5_sm.index]
    top_st = [(int(b), float(corr_st[b])) for b in top5_st.index]

    summary = {
        "Top bands for soil_moisture (nm: r)": [(b, round(r, 4)) for b, r in top_sm],
        "Top bands for soil_temperature (nm: r)": [(b, round(r, 4)) for b, r in top_st],
        "|r| range for soil_moisture": [round(float(corr_sm.abs().min()), 4), round(float(corr_sm.abs().max()), 4)],
        "|r| range for soil_temperature": [round(float(corr_st.abs().min()), 4), round(float(corr_st.abs().max()), 4)],
    }
    return summary


def eda_q3_spectral_profile(df: pd.DataFrame, hyp_bands: list[str], band_wavelengths: list[int], out_dir: str):
    mean_ref = df[hyp_bands].mean()
    std_ref = df[hyp_bands].std()

    fig, ax = plt.subplots(figsize=(13, 4))

    ax.plot(band_wavelengths, mean_ref.values, color="sienna", linewidth=2, label="Mean Reflectance")
    ax.fill_between(
        band_wavelengths,
        mean_ref.values - std_ref.values,
        mean_ref.values + std_ref.values,
        alpha=0.25,
        color="sienna",
        label="±1 Std Dev",
    )

    region_bounds = [
        (454, 500, "Violet", "#7B00D4"),
        (500, 570, "Green", "#007700"),
        (570, 625, "Yel/Org", "#CC7700"),
        (625, 750, "Red", "#AA0000"),
        (750, 950, "NIR", "#555555"),
    ]
    for lo, hi, label, color in region_bounds:
        ax.axvspan(lo, hi, alpha=0.07, color=color)
        ax.text((lo + hi) / 2, 0.245, label, ha="center", va="bottom", fontsize=7.5, color=color)

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Reflectance")
    ax.set_title("Mean Spectral Reflectance Profile of the Soil Sample (±1 Std Dev)")
    ax.legend(fontsize=9)
    ax.set_xlim(454, 950)
    ax.set_ylim(0, 0.27)

    plt.tight_layout()
    out_path = os.path.join(out_dir, "eda_q3_spectral_profile.png")
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "Lowest mean reflectance": (int(mean_ref.idxmin()), round(float(mean_ref.min()), 6)),
        "Highest mean reflectance": (int(mean_ref.idxmax()), round(float(mean_ref.max()), 6)),
        "Std dev range": [round(float(std_ref.min()), 6), round(float(std_ref.max()), 6)],
    }
    return summary


def eda_q4_reflectance_by_day(df: pd.DataFrame, hyp_bands: list[str], band_wavelengths: list[int], out_dir: str):
    # Filter to 11:00-13:59 — the window in the notebook
    df_window = df[df["hour"].isin([11, 12, 13])].copy()

    per_day_mean = df_window.groupby("date")[hyp_bands].mean()
    avg_per_day = per_day_mean.mean(axis=1)

    # Print numeric details (also saved via summary)
    day_stats = []
    for date, val in avg_per_day.items():
        n = int((df_window["date"] == date).sum())
        day_stats.append((str(date), round(float(val), 6), n))

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    fig, ax = plt.subplots(figsize=(13, 4.5))
    for i, (date, row) in enumerate(per_day_mean.iterrows()):
        ax.plot(band_wavelengths, row.values, label=str(date), color=colors[i % len(colors)], linewidth=1.6, alpha=0.85)

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Mean Reflectance")
    ax.set_title("Mean Spectral Reflectance per Day (Observations from 11:00–13:59)")
    ax.legend(title="Date", fontsize=9)
    ax.set_xlim(454, 950)

    plt.tight_layout()
    out_path = os.path.join(out_dir, "eda_q4_reflectance_by_day.png")
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    overall_mean = float(avg_per_day.mean())
    between_day_std = float(avg_per_day.std())
    cv = between_day_std / overall_mean * 100 if overall_mean != 0 else np.nan

    summary = {
        "Mean reflectance per day (date, mean, n_obs_in_window)": day_stats,
        "Overall mean": round(overall_mean, 6),
        "Between-day std": round(between_day_std, 6),
        "Coefficient of variation (%)": round(float(cv), 3),
    }
    return summary


def main():
    input_csv = "soilmoisture_dataset.csv"
    out_dir = "eda_outputs"
    ensure_dir(out_dir)

    if not os.path.exists(input_csv):
        raise FileNotFoundError(
            f"Could not find {input_csv} in the current directory. "
            "Place this script next to soilmoisture_dataset.csv or run from its folder."
        )

    df = pd.read_csv(input_csv, index_col=0)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df["date"] = df["datetime"].dt.date
    df["hour"] = df["datetime"].dt.hour

    hyp_bands, band_wavelengths = get_hyp_band_columns(df)

    print(f"Dataset loaded: {df.shape[0]} observations, {len(hyp_bands)} hyperspectral bands")

    print("\n=== EDA Q1: Soil moisture distribution (normality/outliers) ===")
    q1 = eda_q1_soil_moisture(df, out_dir)
    for k, v in q1.items():
        print(f"{k}: {v}")

    print("\n=== EDA Q2: Band correlations (soil_moisture & soil_temperature) ===")
    q2 = eda_q2_correlations(df, hyp_bands, band_wavelengths, out_dir)
    for k, v in q2.items():
        print(f"{k}: {v}")

    print("\n=== EDA Q3: Mean reflectance profile (wavelength vs reflectance) ===")
    q3 = eda_q3_spectral_profile(df, hyp_bands, band_wavelengths, out_dir)
    for k, v in q3.items():
        print(f"{k}: {v}")

    print("\n=== EDA Q4: Day-to-day reflectance variation at similar times ===")
    q4 = eda_q4_reflectance_by_day(df, hyp_bands, band_wavelengths, out_dir)
    for k, v in q4.items():
        print(f"{k}: {v}")

    print("\nSaved figures to:")
    for fn in [
        "eda_q1_soil_moisture_dist.png",
        "eda_q2_band_correlations.png",
        "eda_q3_spectral_profile.png",
        "eda_q4_reflectance_by_day.png",
    ]:
        print(f"- {os.path.join(out_dir, fn)}")


if __name__ == "__main__":
    main()

