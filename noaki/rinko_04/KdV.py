import os
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # needed for 3D

# るんげくったぱらめた
def kdv_etdrk4(
    Lx: float = 40.0,
    N: int = 512, 
    dt: float = 0.005, 
    tmax: float = 12.0,
    save_steps: int = 300, 
    c: float = 2.0,
    x0: float = 5.0,
):
# KdV方程式を解く！！
    # Grid: 0 から始まる周期区間 x in [0, Lx)
    x = np.linspace(0.0, Lx, N, endpoint=False)

    # Wavenumbers for domain length Lx
    k = 2 * np.pi * np.fft.fftfreq(N, d=Lx / N)
    ik = 1j * k
    L = 1j * k**3  # Linear operator in Fourier space: + i k^3

    # Initial condition: 1-soliton for KdV (coefficient 6)
    # u(x,0) = c/2 * sech^2( sqrt(c)/2 (x - x0) )
    def sech(z):
        return 1.0 / np.cosh(z)

    u = 0.5 * c * sech(0.5 * np.sqrt(c) * (x - x0)) ** 2

    # ETDRK4 precomputations (Kassam & Trefethen 2005)
    E = np.exp(dt * L)
    E2 = np.exp(dt * L / 2)
    M = 16  # contour points for phi functions
    r = np.exp(1j * np.pi * (np.arange(1, M + 1) - 0.5) / M)
    LR = dt * L[:, None] + r[None, :]

    Q = dt * np.mean((np.exp(LR / 2) - 1.0) / LR, axis=1)
    f1 = dt * np.mean(
        (-4 - LR + np.exp(LR) * (4 - 3 * LR + LR**2)) / LR**3,
        axis=1,
    )
    f2 = dt * np.mean(
        (2 + LR + np.exp(LR) * (-2 + LR)) / LR**3,
        axis=1,
    )
    f3 = dt * np.mean(
        (-4 - 3 * LR - LR**2 + np.exp(LR) * (4 - LR)) / LR**3,
        axis=1,
    )

    # Nonlinear term N(u) = -6 u u_x (compute u_x via spectral derivative)
    def nonlinear(u_phys: np.ndarray) -> np.ndarray:
        U = np.fft.fft(u_phys)
        ux = np.fft.ifft(ik * U).real
        return -6.0 * u_phys * ux

    # Time stepping & saving
    Nt = int(np.round(tmax / dt))
    if save_steps > Nt + 1:
        save_steps = Nt + 1
    save_every = max(1, Nt // (save_steps - 1))

    t_save = []
    U_save = []

    def save(tn: float, u_phys: np.ndarray) -> None:
        t_save.append(tn)
        U_save.append(u_phys.copy())

    t = 0.0
    save(t, u)

    U_hat = np.fft.fft(u)
    for n in range(1, Nt + 1):
        Nv = nonlinear(u)
        a = np.fft.ifft(E2 * U_hat + Q * np.fft.fft(Nv)).real
        Na = nonlinear(a)
        b = np.fft.ifft(E2 * U_hat + Q * np.fft.fft(Na)).real
        Nb = nonlinear(b)
        c_stage = np.fft.ifft(
            E * U_hat + Q * np.fft.fft(2 * Nb - Nv)
        ).real
        Nc = nonlinear(c_stage)

        U_hat = (
            E * U_hat
            + np.fft.fft(Nv) * f1
            + 2 * np.fft.fft(Na + Nb) * f2
            + np.fft.fft(Nc) * f3
        )
        u = np.fft.ifft(U_hat).real
        t = n * dt

        if n % save_every == 0 or n == Nt:
            save(t, u)

    U_save = np.array(U_save)
    t_save = np.array(t_save)

    return x, t_save, U_save

# -----------------グラフ描画関数-----------------

def plot_surface(
    x: np.ndarray,
    t: np.ndarray,
    U: np.ndarray,
    out_path: str,
    crest_line: bool = True,
) -> None:
    """3D サーフェスプロットを描画して保存する。"""
    # Create mesh for surface: X: space, Y: time
    X, Y = np.meshgrid(x, t)

    fig = plt.figure(figsize=(6.3,5.4))
    ax = fig.add_subplot(111, projection="3d")

    # 時間軸(Y)を相対的に長く見せるためのアスペクト調整 (x:y:z)
    try:
        ax.set_box_aspect((1.0, 1.4, 0.9))
    except Exception:
        pass

    surf = ax.plot_surface(
        X,
        Y,
        U,
        cmap="viridis",
        linewidth=0,
        antialiased=True,
    )

    # Z軸が見切れないように余白を持たせて設定
    zmin = float(np.min(U))
    zmax = float(np.max(U))
    pad = 0.05 * (zmax - zmin + 1e-12)
    ax.set_zlim(zmin - pad, zmax + pad)

    # 範囲を明示
    ax.set_xlim(float(x.min()), float(x.max()))
    ax.set_ylim(float(t.min()), float(t.max()))

    ax.set_xlabel("x")
    # 標準の y ラベルは隠して独自配置（余白削減）
    ax.set_ylabel("")
    ax.set_zlabel("u", labelpad=10)

    # Z軸ラベルが視点で隠れないように画面基準で回転を固定
    try:
        ax.zaxis.set_rotate_label(False)
        ax.zaxis.label.set_rotation(90)
        ax.zaxis.label.set_color("black")
    except Exception:
        pass

    fig.colorbar(surf, shrink=0.6, aspect=12, pad=0.1)

    if crest_line:
        idxs = np.argmax(U, axis=1)
        x_crest = x[idxs]
        z_crest = U[np.arange(len(t)), idxs]
        ax.plot(
            x_crest,
            t,
            z_crest,
            color="red",
            linewidth=2.0,
            label="crest",
        )
        ax.legend(loc="upper right")

    ax.view_init(elev=22, azim=-95)

    fig.subplots_adjust(left=0.02, right=0.995, bottom=0.1, top=0.93)

    try:
        ax.zaxis.set_rotate_label(False)
        ax.zaxis.label.set_rotation(90)
    except Exception:
        pass

    # timeのラベルの位置！！
    fig.text(
        0.1,
        0.2,
        "time",
        rotation=90,
        va="center",
        ha="center",
        fontsize=10,
    )

    plt.savefig(out_path, dpi=400)
    plt.close(fig)

def main() -> None:
    x, t, U = kdv_etdrk4(
        Lx=40.0,
        N=512,
        dt=0.005,
        tmax=12.0,
        save_steps=300,
        c=2.0,
        x0=5.0,
    )
    out_path = os.path.join(os.path.dirname(__file__), "KdV_surface.png")
    plot_surface(x, t, U, out_path)
    print(f"Saved 3D surface figure: {out_path}")


if __name__ == "__main__":
    main()


