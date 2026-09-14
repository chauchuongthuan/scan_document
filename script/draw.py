import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def plot_cafe_distribution(excel_path):
    """
    Reads Excel data containing 'chum' and 'trai' columns for two measurement periods (T6_2026 & T9_2026)
    and plots probability density distributions (KDE Plot) bounded at zero.
    """
    # 1. Read data from Excel file (Skip title row 1, header starts at row 2)
    df = pd.read_excel(excel_path, header=1)
    
    # Extract data and drop NaN values for each series independently
    t6_chum = df.iloc[:, 0].dropna().astype(float).values  # Col A: T6_2026 chum
    t6_trai = df.iloc[:, 1].dropna().astype(float).values  # Col B: T6_2026 trai
    t9_chum = df.iloc[:, 3].dropna().astype(float).values  # Col D: T9_2026 chum
    t9_trai = df.iloc[:, 4].dropna().astype(float).values  # Col E: T9_2026 trai

    # 2. Setup Plot Style
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=120)
    
    color_t6 = '#2B5C8F'  # Navy Blue for Jun/2026
    color_t9 = '#D9534F'  # Coral Red for Sep/2026

    # -------------------------------------------------------------
    # SUBPLOT 1: DISTRIBUTION OF CLUSTERS / BRANCH (chum)
    # -------------------------------------------------------------
    ax1 = axes[0]
    
    # KDE Curves (clip=(0, None) prevents probability density from stretching below 0)
    sns.kdeplot(t6_chum, ax=ax1, color=color_t6, 
                label=f'Jun/2026 (Mean: {np.mean(t6_chum):.1f})', 
                linewidth=2.5, clip=(0, None), bw_adjust=0.8)
    
    sns.kdeplot(t9_chum, ax=ax1, color=color_t9, 
                label=f'Sep/2026 (Mean: {np.mean(t9_chum):.1f})', 
                linewidth=2.5, linestyle='--', clip=(0, None), bw_adjust=0.8)

    # Median Reference Lines
    ax1.axvline(np.median(t6_chum), color=color_t6, linestyle=':', alpha=0.7, 
                label=f'Jun Median: {np.median(t6_chum):.1f}')
    ax1.axvline(np.median(t9_chum), color=color_t9, linestyle=':', alpha=0.7, 
                label=f'Sep Median: {np.median(t9_chum):.1f}')

    ax1.set_title('Distribution of Clusters', fontsize=13, fontweight='bold', pad=12)
    ax1.set_xlabel('Clusters', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Probability Density', fontsize=11, fontweight='bold')
    ax1.set_xlim(0, max(np.max(t6_chum), np.max(t9_chum)) * 1.15)
    ax1.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    ax1.grid(True, linestyle='--', alpha=0.5)

    # -------------------------------------------------------------
    # SUBPLOT 2: DISTRIBUTION OF FRUITS / CLUSTER (trai)
    # -------------------------------------------------------------
    ax2 = axes[1]
    
    sns.kdeplot(t6_trai, ax=ax2, color=color_t6, 
                label=f'Jun/2026 (Mean: {np.mean(t6_trai):.1f})', 
                linewidth=2.5, clip=(0, None), bw_adjust=0.8)
    
    sns.kdeplot(t9_trai, ax=ax2, color=color_t9, 
                label=f'Sep/2026 (Mean: {np.mean(t9_trai):.1f})', 
                linewidth=2.5, linestyle='--', clip=(0, None), bw_adjust=0.8)

    # Median Reference Lines
    ax2.axvline(np.median(t6_trai), color=color_t6, linestyle=':', alpha=0.7, 
                label=f'Jun Median: {np.median(t6_trai):.1f}')
    ax2.axvline(np.median(t9_trai), color=color_t9, linestyle=':', alpha=0.7, 
                label=f'Sep Median: {np.median(t9_trai):.1f}')

    ax2.set_title('Distribution of Berries', fontsize=13, fontweight='bold', pad=12)
    ax2.set_xlabel('Berries', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Probability Density', fontsize=11, fontweight='bold')
    ax2.set_xlim(0, max(np.max(t6_trai), np.max(t9_trai)) * 1.15)
    ax2.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.suptitle('COFFEE MEASUREMENT DATA COMPARISON: JUN/2026 VS SEP/2026', fontsize=15, fontweight='bold', y=1.03)
    plt.tight_layout()
    plt.show()

# Run function
plot_cafe_distribution("D:/Download/Mau_Du_Lieu_Cafe_T6_T9_KonTum.xlsx")
# plot_cafe_distribution("D:/Download/Mau_Du_Lieu_Cafe_T6_T9_LamHa.xlsx")