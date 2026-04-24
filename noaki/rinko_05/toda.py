import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- 1. Parameter Settings ---

# Circuit parameters
L = 1.0e-6       # Inductance [H] (1 uH)
C0 = 100.0e-12   # Linear capacitance base [F] (100 pF)
V_bias = 5.0     # Varactor bias voltage [V]

# Lattice and Time settings
N = 100          # Number of nodes
T_MAX = 5.0e-7   # Simulation time [s] (500 ns)
T_POINTS = 500   # Time steps for evaluation
times = np.linspace(0, T_MAX, T_POINTS)

# --- 2. Define ODE (Equation of Motion) ---

def toda_lattice_ode(t, y):
    """
    System of ODEs for Toda Lattice.
    y = [Q_1, Q_2, ..., Q_N, P_1, P_2, ..., P_N] (Size: 2N)
    """
    Q = y[:N]  # Charge Q
    P = y[N:]  # Current P (dQ/dt)

    dQdt = P
    dPdt = np.zeros(N)

    # Coefficient: V_bias / L
    V_L_coeff = V_bias / L
    
    # Argument for exp function: Q / (C0 * V_bias)
    Q_norm = Q / (C0 * V_bias) 
    
    # Calculate exponential terms: exp(Q_n / Q0)
    exp_Q = np.exp(Q_norm)

    # --- Equations of Motion ---
    # Boundary Condition: Fixed ends (V=0 outside the lattice -> exp(Q)=1)
    
    # n=0 (Left boundary): Neighbor on left is fixed at 0 (exp=1)
    # V_{n-1} - 2V_n + V_{n+1} -> (1) - 2*exp_Q[0] + exp_Q[1]
    dPdt[0] = V_L_coeff * (1.0 - 2.0 * exp_Q[0] + exp_Q[1])
    
    # n=1 to N-2 (Internal nodes)
    # Using array slicing for speed: P[1:-1] depends on Q[0:-2], Q[1:-1], Q[2:]
    dPdt[1:-1] = V_L_coeff * (exp_Q[0:-2] - 2.0 * exp_Q[1:-1] + exp_Q[2:])
        
    # n=N-1 (Right boundary): Neighbor on right is fixed at 0 (exp=1)
    # V_{n-1} - 2V_n + V_{n+1} -> exp_Q[N-2] - 2*exp_Q[N-1] + (1)
    dPdt[N-1] = V_L_coeff * (exp_Q[N-2] - 2.0 * exp_Q[N-1] + 1.0)
    
    return np.concatenate((dQdt, dPdt))

# --- 3. Initial Conditions (Soliton Pulse) ---

# Parameter for Soliton width/amplitude
kappa = 0.5 
Q0_val = C0 * V_bias

# Calculate Peak Voltage based on kappa
# Soliton solution: V = V_bias * sinh^2(kappa) * sech^2(...)
V_peak_approx = V_bias * np.sinh(kappa)**2

# Convert Voltage peak to Charge peak
Q_peak = Q0_val * np.log(1 + V_peak_approx / V_bias) 

# Initial Charge Distribution Q_n(0)
Q_init = np.zeros(N)
center = N // 4  # Start from the left side to see propagation
k_factor = 1.0   # Factor to adjust width in discrete space
for n in range(N):
    # Approximation of sech^2 shape
    Q_init[n] = Q_peak * (1.0 / np.cosh(k_factor * (n - center)))**2 

# Initial Current P_n(0) = 0
P_init = np.zeros(N)

# Combine initial state
y0 = np.concatenate((Q_init, P_init))

# --- 4. Solve ODE ---

print("Running simulation...")
solution = solve_ivp(
    fun=toda_lattice_ode,
    t_span=[0, T_MAX],
    y0=y0,
    t_eval=times,
    method='RK45'
)
print("Simulation complete.")

# Extract Q results
Q_result = solution.y[:N, :]

# Convert Q to Voltage V
# V_n = V_bias * (exp(Q_n / Q0) - 1)
V_result = V_bias * (np.exp(Q_result / Q0_val) - 1)

# --- 5. Plotting (English Labels) ---

X, T_grid = np.meshgrid(np.arange(N), times)

# Plot 1: 3D Surface Plot
fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(111, projection='3d')

# Plot surface with time in ns
surf = ax.plot_surface(X, T_grid * 1e9, V_result.T, cmap='viridis', edgecolor='none')

ax.set_xlabel('Node Index $n$', fontsize=12)
ax.set_ylabel('Time $t$ [ns]', fontsize=12)
ax.set_zlabel('Voltage $V_n$ [V]', fontsize=12)
ax.set_title(f'Toda Lattice Soliton Propagation ($\\kappa={kappa}$)', fontsize=14)
ax.view_init(elev=25, azim=-120)

cbar = fig.colorbar(surf, ax=ax, pad=0.1, shrink=0.7)
cbar.set_label('Voltage [V]', rotation=270, labelpad=15)

plt.tight_layout()
plt.show()

# Plot 2: 2D Snapshots
plt.figure(figsize=(10, 5))
plot_indices = [0, 100, 200, 300, 400] # Indices to plot

for idx in plot_indices:
    if idx < len(times):
        t_ns = times[idx] * 1e9
        plt.plot(np.arange(N), V_result[:, idx], label=f't = {t_ns:.1f} ns')

plt.xlabel('Node Index $n$', fontsize=12)
plt.ylabel('Voltage $V_n$ [V]', fontsize=12)
plt.title('Soliton Waveform Snapshots', fontsize=14)
plt.legend(loc='upper right')
plt.grid(True, linestyle='--')
plt.tight_layout()
plt.show()