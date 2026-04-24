import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def V_soliton(xi, tau, C, alpha, beta):
    """
    KdVソリトン解: V(xi, tau) = (3C/alpha) * sech^2( 0.5 * sqrt(C/beta) * (xi - C*tau) )
    """
    # 振幅 A = 3C / alpha
    A = 3 * C / alpha
    
    # 幅係数 k = 0.5 * sqrt(C / beta)
    k = 0.5 * np.sqrt(C / beta)
    
    # 位相
    phase = k * (xi - C * tau)
    
    return A * (1.0 / np.cosh(phase))**2

# --- パラメータ設定 ---
alpha = 6.0
beta = 1.0
C = 2.0

# --- グリッド生成 ---
xi = np.linspace(-20, 20, 100)
tau = np.linspace(0, 5, 100)
XI, TAU = np.meshgrid(xi, tau)

# --- 計算 ---
V = V_soliton(XI, TAU, C, alpha, beta)

# --- プロット ---
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# サーフェスプロット
surf = ax.plot_surface(XI, TAU, V, cmap='viridis', edgecolor='none')

# ==========================================
# ラベルとフォントサイズの拡大
# ==========================================
label_size = 22  # 軸ラベルの文字サイズ
tick_size = 14   # 軸の目盛り（数値）の文字サイズ

ax.set_xlabel(r'$\xi$ (Space)', fontsize=label_size, labelpad=15)
ax.set_ylabel(r'$\tau$ (Time)', fontsize=label_size, labelpad=15)
ax.set_zlabel(r'$V$ (Amplitude)', fontsize=label_size, labelpad=15)

ax.tick_params(axis='x', labelsize=tick_size)
ax.tick_params(axis='y', labelsize=tick_size)
ax.tick_params(axis='z', labelsize=tick_size)

cbar = fig.colorbar(surf, shrink=0.5, aspect=5)
cbar.ax.tick_params(labelsize=tick_size)

ax.view_init(elev=30, azim=45)

plt.tight_layout()

# ==========================================
# 修正箇所：背景を透過（transparent=True）して保存
# ==========================================
plt.savefig('solution_plot_transparent.png', dpi=300, bbox_inches='tight', transparent=True)
print("背景透過の高画質画像を保存しました: solution_plot_transparent.png")