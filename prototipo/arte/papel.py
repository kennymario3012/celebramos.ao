import numpy as np
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pnoise(h, w, sigma, rng, aniso=1.0):
    wn = rng.standard_normal((h, w))
    F = np.fft.fft2(wn)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    filt = np.exp(-((fx * aniso) ** 2 + fy ** 2) * (2 * np.pi * sigma) ** 2 / 2)
    out = np.real(np.fft.ifft2(F * filt))
    return (out - out.mean()) / out.std()


def paper(path, base=(247, 237, 235), deep=(238, 227, 210), h=1400, w=900, seed=7, strength=1.0):
    rng = np.random.default_rng(seed)
    blot = pnoise(h, w, 70, rng)
    mid = pnoise(h, w, 16, rng)
    fine = pnoise(h, w, 1.1, rng)
    fib = pnoise(h, w, 3.0, rng, aniso=0.18)
    L = strength * (0.009 * blot + 0.004 * mid + 0.008 * fine + 0.004 * fib)
    b = np.array(base, dtype=float)[None, None, :] / 255
    # variação no mesmo tom: as manchas puxam ligeiramente para a cor `deep`, nunca para cinzento ou verde
    deep = np.array(deep, dtype=float)[None, None, :] / 255
    t = np.clip(0.18 + 0.12 * blot, 0, 1)[..., None] * strength
    img = np.clip((b * (1 - t) + deep * t) * (1 + L[..., None]), 0, 1)
    Image.fromarray((img * 255).astype(np.uint8)).save(path, "WEBP", quality=78, method=6)
    print(path, Path(path).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    paper(ROOT / "papel-teste.webp")
