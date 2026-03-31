from __future__ import annotations

import numpy as np
from fbm import FBM


class FractionalBrownianBridge:

    def __init__(self, hurst: float = 0.45):
        self.hurst = hurst

    def generate_bridge(
        self,
        start: float,
        end: float,
        n_steps: int,
        seed: int | None = None
    ) -> np.ndarray:
        if n_steps <= 0:
            return np.array([])
        if n_steps == 1:
            return np.array([start])

        if seed is not None:
            np.random.seed(seed)

        fbm_gen = FBM(n=n_steps-1, hurst=self.hurst, length=1.0, method='daviesharte')
        fbm_increments = fbm_gen.fbm()

        fbm_increments = fbm_increments - fbm_increments[0]
        t = np.linspace(0, 1, len(fbm_increments))
        fbm_increments = fbm_increments - t * fbm_increments[-1]

        normalized = fbm_increments / (np.max(np.abs(fbm_increments)) + 1e-10)

        path = np.linspace(start, end, n_steps)

        drift_component = path
        diffusion_component = normalized * abs(end - start) * 0.3

        bridge = drift_component + diffusion_component

        bridge[0] = start
        bridge[-1] = end

        return bridge

    def generate_constrained_path(
        self,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        n_ticks: int,
        high_touch_time: float,
        low_touch_time: float,
        seed: int | None = None
    ) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)

        high_idx = int(high_touch_time * n_ticks)
        low_idx = int(low_touch_time * n_ticks)

        high_idx = max(1, min(n_ticks - 2, high_idx))
        low_idx = max(1, min(n_ticks - 2, low_idx))

        if high_idx == low_idx:
            if high_idx < n_ticks - 2:
                low_idx = high_idx + 1
            else:
                low_idx = high_idx - 1

        segments = []

        seed1 = (seed * 3 + 1) % (2**32) if seed is not None else None
        seed2 = (seed * 3 + 2) % (2**32) if seed is not None else None
        seed3 = (seed * 3 + 3) % (2**32) if seed is not None else None

        if high_touch_time < low_touch_time:
            seg1 = self.generate_bridge(open_price, high_price, high_idx, seed1)
            seg2 = self.generate_bridge(high_price, low_price, low_idx - high_idx + 1, seed2)
            seg3 = self.generate_bridge(low_price, close_price, n_ticks - low_idx + 1, seed3)
            segments = [seg1, seg2[1:], seg3[1:]]
        else:
            seg1 = self.generate_bridge(open_price, low_price, low_idx, seed1)
            seg2 = self.generate_bridge(low_price, high_price, high_idx - low_idx + 1, seed2)
            seg3 = self.generate_bridge(high_price, close_price, n_ticks - high_idx + 1, seed3)
            segments = [seg1, seg2[1:], seg3[1:]]

        path = np.concatenate(segments)

        path = np.clip(path, low_price, high_price)

        path[0] = open_price
        path[-1] = close_price

        return path
