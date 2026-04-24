import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def calculate_current(t, E, R, L, I_init):
    """RL回路の電流計算 (ON期間)"""
    return E/R + (I_init - E/R) * np.exp(-(R/L)*t)

def calculate_freewheel(t, R, L, I_init):
    """還流区間の電流計算 (OFF期間)"""
    return I_init * np.exp(-(R/L)*t)

def simulate_waveform(E, R, L, f, d, t_max, num_points=2000):
    """指定されたパラメータで波形データを生成する関数"""
    T = 1.0 / f
    Ton = d * T
    tau = L / R
    
    # 定常状態のI_min, I_max理論値計算
    I_max = (E/R) * (1 - np.exp(-Ton/tau)) / (1 - np.exp(-T/tau))
    I_min = (E/R) * (np.exp(Ton/tau) - 1) / (np.exp(T/tau) - 1)
    
    t_vals = np.linspace(0, t_max, num_points)
    i_vals = []
    
    # シミュレーション実行
    # t_valsの各点について、その時刻がサイクルのどこにあるかを判定して計算
    for t in t_vals:
        t_cycle = t % T # 周期内の時刻
        
        # 定常状態なので、開始電流はサイクルの位置によって決まる
        # ただし、厳密には前のサイクルの続きだが、理論値I_min/I_maxがわかっているので
        # 各サイクル独立して計算可能
        
        if t_cycle <= Ton:
            val = calculate_current(t_cycle, E, R, L, I_min)
        else:
            val = calculate_freewheel(t_cycle - Ton, R, L, I_max)
        i_vals.append(val)
        
    return t_vals, np.array(i_vals), I_min, I_max

# --- メイン処理 ---

# 基本パラメータ
E = 100.0
R = 10.0
L_base = 1e-3  # 1mH
f_base = 10e3  # 10kHz
d = 0.5
T_base = 1 / f_base

# グラフ描画用時間 (基本周波数の2周期分 = 200us)
t_display_max = 2 * T_base

# 1. 課題4: 基本波形 (10kHz, 1mH)
t_base, i_base, _, _ = simulate_waveform(E, R, L_base, f_base, d, t_display_max)

# 電圧波形の作成（表示用）
v_base = []
for t in t_base:
    if (t % T_base) <= (d * T_base):
        v_base.append(E)
    else:
        v_base.append(0)

fig, ax1 = plt.subplots(figsize=(10, 6))
color = 'tab:blue'
ax1.set_xlabel('Time [s]')
ax1.set_ylabel('Load Current [A]', color=color)
ax1.plot(t_base, i_base, color=color, label='Current')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True)

ax2 = ax1.twinx()
color = 'tab:orange'
ax2.set_ylabel('Output Voltage [V]', color=color)
ax2.plot(t_base, v_base, color=color, linestyle='--', alpha=0.5, label='Voltage')
ax2.tick_params(axis='y', labelcolor=color)

plt.title(rf'Waveforms (E={E}V, R={R}$\Omega$, L={L_base*1000}mH, f={f_base/1000}kHz)')
fig.tight_layout()
plt.savefig('waveform.png')
plt.close()

# CSV出力
pd.DataFrame({'Time[s]': t_base, 'Voltage[V]': v_base, 'Current[A]': i_base}).to_csv('id_waveforms.csv', index=False)
print("Task 4: Saved waveform.png and csv.")


# 2. 課題5: デューティー比 vs 平均電圧
d_list = np.arange(0, 1.1, 0.1)
v_avg_list = d_list * E

plt.figure(figsize=(8, 6))
plt.plot(d_list, v_avg_list, marker='o')
plt.xlabel('Duty Factor d')
plt.ylabel('Average Output Voltage [V]')
plt.title('Duty Factor vs Average Output Voltage')
plt.grid(True)
plt.savefig('avg_voltage.png')
plt.close()

pd.DataFrame({'DutyFactor': d_list, 'AvgVoltage[V]': v_avg_list}).to_csv('id_avg_voltage.csv', index=False)
print("Task 5: Saved avg_voltage.png and csv.")


# 3. 課題6a: インダクタンス比較 (L=1mH vs 10mH)
L_large = 10e-3 # 10mH
_, i_largeL, _, _ = simulate_waveform(E, R, L_large, f_base, d, t_display_max)

plt.figure(figsize=(10, 6))
plt.plot(t_base, i_base, label=rf'Original (L={L_base*1000}mH)')
plt.plot(t_base, i_largeL, label=rf'Large L (L={L_large*1000}mH)')
plt.xlabel('Time [s]')
plt.ylabel('Load Current [A]')
plt.title(rf'Ripple Reduction by Increasing Inductance (f={f_base/1000}kHz)')
plt.legend()
plt.grid(True)
plt.savefig('ripple_comparison_L.png')
plt.close()
print("Task 6a: Saved ripple_comparison_L.png")


# 4. 課題6b: 周波数比較 (f=10kHz vs 100kHz)
f_high = 100e3 # 100kHz (10倍)
_, i_highF, _, _ = simulate_waveform(E, R, L_base, f_high, d, t_display_max)

plt.figure(figsize=(10, 6))
plt.plot(t_base, i_base, label=rf'Original (f={f_base/1000}kHz)')
plt.plot(t_base, i_highF, label=rf'High Freq (f={f_high/1000}kHz)')
plt.xlabel('Time [s]')
plt.ylabel('Load Current [A]')
plt.title(rf'Ripple Reduction by Increasing Frequency (L={L_base*1000}mH)')
plt.legend()
plt.grid(True)
plt.savefig('ripple_comparison_F.png')
plt.close()
print("Task 6b: Saved ripple_comparison_F.png")

print("\nAll tasks completed.")