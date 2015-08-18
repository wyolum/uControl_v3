import matplotlib; matplotlib.interactive(True)
import util
from constants import *
from pylab import *
from numpy import *


SBP = 120      ## mmHg
DBP = 80       ## mmHg
PMID = (DBP + DBP) / 2.

PP = SBP - DBP ## mmHg
MAP = 105      ## mmHg
HR = 80 / 60.  ## pulse per sec (a.k.a f)
OMEGA = 2 * pi * HR
PULSE_PRESSURE = SBP - DBP

V0 = 85       ## ml
Va0 = .3       ## ml
P0 = 150       ## mmHg
R0 = 3.        ## mmHg / S
# R0 = 2.        ## mmHg / S

A = .05        ## per mmHg
B = .03        ## per mmHg

r_artery = .2
delta_r_artery = .04 * r_artery
l_artery = 10
deltaVa_n = 2 * pi * r_artery * delta_r_artery * l_artery
# Cn = deltaVa_n / PP
# print Cn

Pamb = 760     ## mmHg

OVERSAMPLE = 1
DT = defaults['dt'] / OVERSAMPLE

Tmax = 140

LP_TAPS = util.get_lowpass_taps(defaults['high_cuttoff_hz'], 
                                defaults['dt'],
                                defaults['n_tap'])
LLP_TAPS = util.get_lowpass_taps(defaults['low_cuttoff_hz'], 
                                 defaults['dt'],
                                 defaults['n_tap'])

T_OFFSET = .123123

def smooth_dP_dt(t, r0, p0):
    '''
    return average pressure change rate as a function of t
    '''
    return -r0 * exp(-(r0 / p0) * t)

def smooth_P(t, r0, p0):
    return P0 * exp(-(r0  / p0) * t)

def Pa(t):
    out =  (sin(OMEGA * t) + 1. * sin(2 * OMEGA * t) + .25 * sin(3 * OMEGA * t))
    out *= .5/max(abs(out))
    out *= 1 + .1 * sin(.251231231 * HR * 2 * pi * t)
    return DBP + PULSE_PRESSURE/2 + PULSE_PRESSURE * out
    return DBP + .5 * PULSE_PRESSURE+ .36 * PULSE_PRESSURE  * (sin(OMEGA * t) + .5 * sin(2 * OMEGA * t) + .25 * sin(3 * OMEGA * t))

def dPa_dt(t):
    f = Pa(t)
    out = zeros(len(f))
    out[1:] = diff(f) / diff(t)
    out[0] = out[1]
    return out  ## use numeric diff
    return .36 * PULSE_PRESSURE * OMEGA * (cos(OMEGA * t) + cos(2 * OMEGA * t) + .75 * cos(3 * OMEGA * t))

def dVa_dP(Pt, a, b):
    '''Arterial compliance!'''
    ntr = (Pt < 0)
    ptr = (Pt >= 0)
    return (a * Va0 * exp(a * Pt) * ntr + 
            a * Va0 * exp(-b * Pt) * ptr)
def Va(Pt, a, b):
    return cumsum(dVa_dP(Pt, a, b)) * (Pt[1] - Pt[0])

def dVa_dt(t, r0, p0, a, b):
    '''eqns (6a) and (6b)'''
    Pt = (Pa(t) - smooth_P(t, r0, p0)) ### flow
    # plot(Pt)
    # plot((Pa(t) - P0 + r * t))
    # raw_input('[...'); here
    _r = smooth_dP_dt(t, r0, p0)
    ntr = (Pt < 0)
    ptr = (Pt >= 0)
    
    dV_dP =  (a * Va0 * exp( a * Pt) * ntr + 
              a * Va0 * exp(-b * Pt) * ptr) 
    return dVa_dP(Pt, a, b) * (dPa_dt(t) + _r)

def dP_dt(t, r0, p0, a, b):
    ''' eqn (1a)'''
    _r = -smooth_dP_dt(t, r0, p0)
    xx = P0 -smooth_P(t, r0, p0)
    return -_r + (P0 + Pamb - xx) / (V0) * dVa_dt(t, r0, p0, a, b)

t = arange(0, Tmax, DT)

def P(t, r0, p0, a, b):
    return P0 + cumsum(dP_dt(t, r0, p0, a, b)) * DT

IDX = slice(None, None, OVERSAMPLE)
Pt1 = P(t, R0, P0, A, B)[IDX]
Pt2 = P(t + .5/HR, R0, P0, A, .75 * B)[IDX]

lp1 = util.filter(Pt1 - Pt1[0], LP_TAPS) + Pt1[0]
llp1 = util.filter(Pt1 - Pt1[0], LLP_TAPS) + Pt1[0]

lp2 = util.filter(Pt2 - Pt2[0], LP_TAPS) + Pt2[0]
llp2 = util.filter(Pt2 - Pt2[0], LLP_TAPS) + Pt2[0]

XX = (smooth_P(t[IDX], R0, P0) - P0)
fixup = -util.filter(XX, LP_TAPS - LLP_TAPS)

bpf1 = lp1 - llp1 + fixup
bpf2 = lp2 - llp2 + fixup

if False:
    figure(1)
    subplot(212)
    plot(t, smooth_P(t, R0, P0))
    plot(t, P0 + cumsum(smooth_dP_dt(t, R0, P0)) * DT)
    ylabel('smooth pressure')
    subplot(211)
    plot(t, smooth_dP_dt(t, R0, P0))
    xlabel('$t$')
    ylabel('smooth dP/dt')

if False:
    figure(2)
    _Pt = arange(-50, 200, 1)
    subplot(211)
    plot(_Pt, Va(_Pt, A, B))
    title(r'$V_a$ vs. TransmuralP')
    subplot(212)
    plot(_Pt, dVa_dP(_Pt, A, B))

if False:
    figure(3); 
    plot(t, dP_dt(t, R0, P0, A, B))
    xlabel('$t$ Second')
    ylabel(r'$\frac{dP}{dt}$ mmHg/Second')


    plot(t, dP_dt(t, R0, P0, A, B))
    xlabel('$t$ Second')
    ylabel(r'$\frac{dP}{dt}$ mmHg/Second')
if True:
    figure(4); 
    subplot(211)
    # plot(t, P(t, R0, P0, A, B))
    # plot(t, Pt1)
    plot(t[IDX], lp1)
    # plot(t[IDX], llp1)
    # plot(t, Pt2)
    # plot(t[IDX], lp2)
    # plot(t[IDX], llp2)
    plot(t, Pa(t))
    plot([0, t[-1]], [DBP, DBP], '--')
    plot([0, t[-1]], [SBP, SBP], '--')
    ylabel(r'$P$ mmHg')


    subplot(212)
    plot(t[IDX], bpf1)
    # plot(t[IDX], bpf2)
    ylabel(r'filtered pressure mmHg')

    xlabel('$t$ Second')

raw_input('...')
