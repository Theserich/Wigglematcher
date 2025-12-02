import jax.numpy as jnp
from jax.scipy.special import logsumexp
from jax.scipy.stats import norm
from jax import jit
from matplotlib import pyplot as plt
from time import time

from PyQt5.QtWidgets import QApplication

import numpy as np
#import jax.numpy as jnp
#from jax.scipy.special import logsumexp
#from jax.scipy.stats import norm
#from matplotlib import pyplot as plt
#from jax import jit
from src.timer import timer

def jax_interp1d(x_data, y_data):
    x_data = jnp.asarray(x_data)
    y_data = jnp.asarray(y_data)

    def interpolator(x):
        return jnp.interp(x, x_data, y_data)

    return interpolator


@jit
def bayesian_wiggler_offset_jax(wigglefms, wigglefms_sig,
                                active_idx, testoffsets,
                                R, dR, offsetprior):
    wigglefms = jnp.asarray(wigglefms)
    wigglefms_sig = jnp.asarray(wigglefms_sig)
    active_idx = jnp.asarray(active_idx)
    testoffsets = jnp.asarray(testoffsets)
    offsetprior = jnp.asarray(offsetprior)
    dRi = wigglefms_sig[:, None][None, :, :]                # (1, len_wig, 1)
    offsets = testoffsets[:, None, None]                    # (len_off, 1, 1)
    ages = -8033 * jnp.log(wigglefms[None, :, None]) + offsets
    Ri = jnp.exp(-ages / 8033.0)                            # (len_off, len_wig, 1)
    denom = (2 * dRi**2 + 2 * dR**2)
    ps_loglikelihoods = (-(Ri - R) ** 2 / denom
                         - 0.5 * jnp.log(2 * jnp.pi * (dRi**2 + dR**2)))
    log_offsets_prior = jnp.log(offsetprior)[:, None, None]   # (len_off,1,1)
    weighted_ps_loglikelihoods = ps_loglikelihoods + log_offsets_prior
    active_mask = jnp.where(active_idx, 1.0, 0.0)   # (len_wig,)
    loglikelyhoods = jnp.sum(weighted_ps_loglikelihoods * active_mask[None, :, None], axis=1)
    likelyhoods = jnp.exp(loglikelyhoods - jnp.max(loglikelyhoods))
    posterior_age_log = logsumexp(loglikelyhoods, axis=0)
    posterior_offset_log = logsumexp(loglikelyhoods, axis=1)
    posterior_age = jnp.exp(posterior_age_log - logsumexp(posterior_age_log))
    posterior_offset = jnp.exp(posterior_offset_log - logsumexp(posterior_offset_log))
    posterior_offset_log_expanded = posterior_offset_log[:, None, None]
    posterior_ps_loglikelihoods = ps_loglikelihoods + posterior_offset_log_expanded
    log_ps = logsumexp(posterior_ps_loglikelihoods, axis=0)
    ps = jnp.exp(log_ps - logsumexp(log_ps, axis=1, keepdims=True))
    A_is = jnp.sum(posterior_age * ps, axis=1) / jnp.sum(ps**2, axis=1)
    A_overall = jnp.exp(jnp.mean(jnp.log(A_is)))
    n_active = jnp.sum(active_idx)
    A_n = 1 / (2 * n_active) ** 0.5
    return posterior_age, posterior_offset,ps_loglikelihoods, likelyhoods, ps, A_overall,A_is, A_n



@jit
def calc_ps_loglikelihoods(wigglefms,wigglefms_sig,testoffsets,R,dR):
    dRi = wigglefms_sig[:, None][None, :, :]  # (1, len_wig, 1)
    offsets = testoffsets[:, None, None]  # (len_off, 1, 1)
    ages = -8033 * jnp.log(wigglefms[None, :, None]) + offsets
    Ri = jnp.exp(-ages / 8033.0)  # (len_off, len_wig, 1)
    denom = (2 * dRi ** 2 + 2 * dR ** 2)
    ps_loglikelihoods = (-(Ri - R) ** 2 / denom - 0.5 * jnp.log(2 * jnp.pi * (dRi ** 2 + dR ** 2)))
    return ps_loglikelihoods

@jit
def calc_posterior(ps_loglikelihoods,offsetprior,active_idx):
    log_offsets_prior = jnp.log(offsetprior)[:, None, None]  # (len_off,1,1)
    weighted_ps_loglikelihoods = ps_loglikelihoods + log_offsets_prior
    active_mask = jnp.where(active_idx, 1.0, 0.0)  # (len_wig,)
    loglikelyhoods = jnp.sum(weighted_ps_loglikelihoods * active_mask[None, :, None], axis=1)
    likelyhoods = jnp.exp(loglikelyhoods - jnp.max(loglikelyhoods))
    posterior_age_log = logsumexp(loglikelyhoods, axis=0)
    posterior_offset_log = logsumexp(loglikelyhoods, axis=1)
    posterior_age = jnp.exp(posterior_age_log - logsumexp(posterior_age_log))
    posterior_offset = jnp.exp(posterior_offset_log - logsumexp(posterior_offset_log))
    posterior_offset_log_expanded = posterior_offset_log[:, None, None]
    posterior_ps_loglikelihoods = ps_loglikelihoods + posterior_offset_log_expanded
    log_ps = logsumexp(posterior_ps_loglikelihoods, axis=0)
    ps = jnp.exp(log_ps - logsumexp(log_ps, axis=1, keepdims=True))
    A_is = jnp.sum(posterior_age * ps, axis=1) / jnp.sum(ps ** 2, axis=1)
    A_overall = jnp.exp(jnp.mean(jnp.log(A_is)))
    n_active = jnp.sum(active_idx)
    A_n = 1 / (2 * n_active) ** 0.5
    return posterior_age, posterior_offset, likelyhoods, ps, A_overall,A_is, A_n


@jit
def get_year_mask(curvefm, curvefm_sig, wigglefms, wigglefms_sig, testoffsets):
    curveage = -8033 * jnp.log(curvefm)
    curveage_sig = 8033/curvefm*curvefm_sig
    wigfgleages = -8033 * jnp.log(wigglefms)
    wigfgleages_sig = 8033/wigglefms*wigglefms_sig
    minsearch = jnp.min(wigfgleages) - 5*jnp.max(wigfgleages_sig)-jnp.abs(jnp.min(testoffsets))
    maxsearch = jnp.max(wigfgleages) + 5*jnp.max(wigfgleages_sig)+jnp.abs(jnp.max(testoffsets))
    mask = (curveage - curveage_sig <= maxsearch) & (curveage + curveage_sig >= minsearch)
    return mask




