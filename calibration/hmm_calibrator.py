from __future__ import annotations

import logging
from typing import Dict

import numpy as np
import pandas as pd
import yfinance as yf
from hmmlearn import hmm

from utils.types import HMMParams

logger = logging.getLogger(__name__)


class HMMCalibrator:
    
    def __init__(self, n_states: int = 4):
        self.n_states = n_states
    
    def download_data(self, ticker: str) -> pd.DataFrame:
        logger.info(f"Downloading historical data for {ticker}")
        data = yf.download(ticker, period="max", progress=False, auto_adjust=True)
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        return data
    
    def calculate_returns(self, data: pd.DataFrame) -> np.ndarray:
        close_prices = data['Close'].values
        returns = np.log(close_prices[1:] / close_prices[:-1])
        return returns
    
    def fit_hmm(self, returns: np.ndarray) -> hmm.GaussianHMM:
        returns_reshaped = returns.reshape(-1, 1)
        
        model = hmm.GaussianHMM(
            n_components=self.n_states,
            covariance_type="full",
            n_iter=1000,
            random_state=42
        )
        
        logger.info(f"Fitting HMM with {self.n_states} states")
        model.fit(returns_reshaped)
        
        return model
    
    def extract_params(self, model: hmm.GaussianHMM) -> HMMParams:
        transition_matrix = model.transmat_.tolist()
        means = model.means_.flatten().tolist()
        
        stds = []
        for i in range(self.n_states):
            cov = model.covars_[i]
            if cov.ndim == 2:
                std = float(np.sqrt(cov[0, 0]))
            else:
                std = float(np.sqrt(cov))
            stds.append(std)
        
        start_probs = model.startprob_.tolist()
        
        return HMMParams(
            n_states=self.n_states,
            transition_matrix=transition_matrix,
            means=means,
            stds=stds,
            start_probs=start_probs
        )
    
    def validate_regimes(self, params: HMMParams) -> Dict[int, str]:
        regime_labels = {}
        
        sorted_indices = sorted(
            range(len(params.stds)),
            key=lambda i: params.stds[i]
        )
        
        for idx, state_idx in enumerate(sorted_indices):
            if idx == 0:
                regime_labels[state_idx] = "low-vol"
            elif idx == 1:
                regime_labels[state_idx] = "normal"
            elif idx == 2:
                regime_labels[state_idx] = "high-vol"
            else:
                regime_labels[state_idx] = "extreme"
        
        logger.info("Regime characteristics:")
        for state_idx, label in regime_labels.items():
            logger.info(
                f"  State {state_idx} ({label}): "
                f"μ={params.means[state_idx]:.6f}, "
                f"σ={params.stds[state_idx]:.6f}"
            )
        
        return regime_labels
    
    def calibrate(self, ticker: str) -> HMMParams:
        data = self.download_data(ticker)
        returns = self.calculate_returns(data)
        
        logger.info(f"Fitting HMM on {len(returns)} daily returns")
        
        model = self.fit_hmm(returns)
        params = self.extract_params(model)
        
        self.validate_regimes(params)
        
        return params
