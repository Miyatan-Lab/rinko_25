#!/usr/bin/env python3
import os

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # needed for 3D


def kdv_soliton_simple(
    Lx: float = 40.0,
    N: int = 512,
    tmax: float = 4.0,
    save_steps: int = 200,
):
    """
    KdV: u_t + 6 u u_x + u_{xxx} = 0 の 1 ソリトンの
    一番シンプルな形

        u(x,t) = 2 sech^2(x - 4 t)

    をそのまま評価して返すだけの関数。

    Parameters
    ----------
    Lx : float
        空間区間の長さ（x ∈ [-Lx/2, Lx/2)）
    N : int
        空間分割数
    tmax : float
        最終時刻
    save_steps : int
        保存する時刻の数

    Returns
    -------
    x : ndarray, shape (N,)
        空間グリッド
    t_save : ndarray, shape (save_steps,)
        時刻グリッド
    U_save : ndarray, shape (save_steps, N)
        各時刻の u(x,t)
    """
    # 空間グリッド（中央にソリトンが来やすいよう [-Lx/2, Lx/2)）
    x = np.linspace(-Lx / 2.0, Lx / 2.0, N, endpoint=False)

    # 時間グリッド（等間隔）
    t_save = np.linspace(0.0, tmax, save_steps)

    # メッシュを作って一気に評価
    X, T = np.meshgrid(x, t_save)

    # ★ u の定義をできるだけ簡単に：
    #     u(x,t) = 2 * sech^2(x - 4 t)
    phase = X - 4.0 * T
    U_save = 2.0 / np.cosh(phase) ** 2

    return x, t_save, U_save


def plot_surface(
    x: np.ndarray,
    t: np.ndarray,
    U: np.ndarray,
    out_path: str,
    crest_line: bool = True,
) -> None:
    """3D サーフェスプロットを描画して保存する。"""
    X, Y = np.meshgrid(x, t)

    # ほぼ正方形の図にして横長感を減らす
    fig = plt.figure(figsize=(5.0, 5.0))
    ax = fig.add_subplot(111, projection="3d")

    # 時間軸(Y)を多少強調（なくてもOK）
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

    # Z軸が見切れないように余白
    zmin = float(np.min(U))
    zmax = float(np.max(U))
    pad = 0.05 * (zmax - zmin + 1e-12)
    ax.set_zlim(zmin - pad, zmax + pad)

    ax.set_xlim(float(x.min()), float(x.max()))
    ax.set_ylim(float(t.min()), float(t.max()))

    ax.set_xlabel("x")
    ax.set_ylabel("time")
    ax.set_zlabel("u", labelpad=10)

    try:
        ax.zaxis.set_rotate_label(False)
        ax.zaxis.label.set_rotation(90)
        ax.zaxis.label.set_color("black")
    except Exception:
        pass

    fig.colorbar(surf, shrink=0.7, aspect=16, pad=0.1)

    # 山頂の軌跡（x vs t）を描いて、ソリトンの移動を明示
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

    fig.subplots_adjust(left=0.15, right=0.98, bottom=0.12, top=0.96)

    plt.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> None:
    x, t, U = kdv_soliton_simple(
        Lx=40.0,
        N=512,
        tmax=4.0,
        save_steps=200,
    )
    out_path = os.path.join(os.path.dirname(__file__), "KdV_soliton_surface_simple.png")
    plot_surface(x, t, U, out_path)
    print(f"Saved 3D surface figure: {out_path}")


if __name__ == "__main__":
    main()
