'''
Try filtering deltas to within +- 200% forward and backward
'''

import glob
import csv
import os.path
import sys
import pickle
import time
from  pylab import *
from numpy import *

from constants import *
import util
import scipy.interpolate.interpolate as interp
import scipy.integrate

## Filter taps
LP_TAPS = util.get_lowpass_taps(defaults['high_cuttoff_hz'], 
                                defaults['dt'],
                                defaults['n_tap'])
LLP_TAPS = util.get_lowpass_taps(defaults['low_cuttoff_hz'], 
                                 defaults['dt'],
                                 defaults['n_tap'])
DELAY_TAPS = zeros(defaults['n_tap'])
DELAY_TAPS[defaults['n_tap'] // 2] = 1

def get_flow(gage, cba):
    c, b, a = cba
    return (-b + sqrt(b ** 2 - 4 * a * (c - gage))) / (2 * a)


def flow_of_gage(flow, gage, cba=None):
    '''
    return the quadratic smoothed flow values
    
    flow -- flow measurements corrected for temp and pressure
    gage -- gage pressure measurements
    '''
    flow = array(flow)
    keep = (flow > 50)
    keep = arange(len(flow))
    __flow = flow[keep]
    __gage = array(gage)[keep]

    N = len(__flow)
    A = array(zip(ones(len(keep)), __flow, __flow ** 2))
    if cba is None:
        cba = dot(linalg.inv(dot(A.T, A)), dot(A.T, __gage))
    flow_fit = get_flow(gage, cba)
    # plot(gage, flow)
    # plot(gage, flow_fit)
    # show(); here
    return flow_fit, cba

def ideal_gas_compliance(gage_p, v0):
    return v0 / (gage_p + 760.)

def flow_correction(flow, gage_p, amb_p, amb_t):
    '''
    From Pramod: 
    (P_s/T_s) x (T_true/P_true)
    where Q_s is the output of the flow sensor, 
    P_s = 1013 mbar, 
    T_s = 293 K,  
    P_true = P_ambient + P_gage, 
    T_true is the output of the temperature sensor.
    '''
    P_s = 760 #  * mmhg
    T_s = 293.15  # K
    if amb_p is None:
        amb_p = P_s
    P_true = amb_p + gage_p
    T_true = amb_t + 273.15 # K
    ambient_correction_factor = (P_s * T_true) / (T_s * P_true)
    out = flow * ambient_correction_factor
    return out

def rfreqs(Nsample, dt):
    freqs = fft.fftfreq(Nsample, dt)
    return freqs[freqs >= 0]

def get_arterial_compliance(flow, low_low_pass_gage, low_pass_gage,
                            amb_temperature, amb_pressure, MAP=None, SBP=None, DBP=None, cba=None):
    pressure = amb_pressure + low_pass_gage
    flow_fit, cba = flow_of_gage(flow, low_low_pass_gage, cba)
    corrected_flow = flow_correction(flow_fit, 
                                     low_low_pass_gage, 
                                     amb_pressure, 
                                     amb_temperature)

    t = arange(len(corrected_flow)) * defaults['dt']

    wvol = cumsum(flow_fit)  * defaults['dt'] / 60.         ### best fit

    t = arange(len(wvol)) * defaults['dt']

    keep = (low_low_pass_gage < 30)
    x = flow / 60.
    y = low_low_pass_gage
    k = 3.
    A = x ** k
    b = dot(A, y) / dot(A, A)
    yfit = A * b
    xfit = ((y/b) ** (1. / k))
    t = arange(len(y)) * defaults['dt']

    my_gage = arange(160)
    c, b, a = cba
    

    cuff_compl = corrected_flow[:-1] * (defaults['dt'] / diff(low_low_pass_gage)) / 60.
   
    bpf = low_pass_gage - low_low_pass_gage
    v_of_p = interp.interp1d(low_low_pass_gage[::-1], wvol[::-1], bounds_error=False)

    peaks, troughs = util.find_pulse_peaks_and_troughs(bpf, 1, .005)
    if peaks[0] < troughs[0]: # peak follows trough
        peaks = peaks[1:]
    if troughs[-1] > peaks[-1]: # peak follows trough
        troughs = troughs[:-1]
    hills = []
    for trough, peak in zip(troughs, peaks): ## filter loong pulses
        if (peak - trough) * defaults['dt'] < MAX_PULSE:
            hills.append((trough, peak))
    assert len(peaks) == len(troughs)
    hills = array(hills)
    troughs = hills[:,0]
    peaks = hills[:,1]
    
    delta_vs = []
    deltav_ps = []
    deltav_ts = []
    cuff_pressures = []

    for t, p in hills:
        cuff_pressure = (low_low_pass_gage[p] + low_low_pass_gage[t])/2.
        delta_v =ideal_gas_compliance(low_low_pass_gage[p], wvol[-1])  *  (bpf[p] - bpf[t])
        delta_vs.append(delta_v)
        cuff_pressures.append(cuff_pressure)

    p = arange(v_of_p.x[0], v_of_p.x[-1], 1)
    dv_dp_cuff = diff(v_of_p(p)) / diff(p)
    A = 1./p[1:]
    y = dv_dp_cuff
    c = dot(A, y) / dot(A, A)

    ### find largest delta for p6 fit.
    deltas = bpf[peaks] - bpf[troughs]
    candidate_deltas = [d for idx, d in zip(peaks, deltas) if low_low_pass_gage[idx] > 60] ## MAP must be above 60mmhg.
    n_peak = argmax(candidate_deltas) * 2 + 1
    # n_peak = len(peaks) - 1
    if n_peak >= len(peaks):
        n_peak = len(peaks)
    # n_peak = argmax(bpf[peaks] - bpf[troughs]) * 3
    if n_peak < 15:
        if len(peaks) < 15:
            n_peak = len(peaks) - 1
        else:
            n_peak = 15
    assert n_peak <= len(peaks)
    deltas = bpf[peaks] - bpf[troughs]
    idx = arange(len(deltas))
    # plot(idx, deltas)
    if False: ## filter out noisy peaks?
        keep = util.filter_deltas(idx, deltas, .3)
    else:# keep all
        keep = idx
    # plot(keep, deltas[keep])
    hills = hills[keep]
    troughs = troughs[keep]
    peaks = peaks[keep]
    deltas = deltas[keep]
    delta_vs = array(delta_vs)[keep]
    max_delta_i = argmax(deltas)

    if MAP is None:
        # MAP = low_pass_gage[hills[max_delta_i][1]]

        ### compute map6
        MAP_ii = argmax(deltas)
        MAP_i = hills[MAP_ii][1]
        # MAP = low_low_pass_gage[MAP_i]
        
        if True:
            p6 = util.poly_fit(troughs[:n_peak] * defaults['dt'], deltas[:n_peak], 6) ### Actual
            # p6 = util.poly_fit(troughs[:] * defaults['dt'], deltas[:], 6)             ### Test
        else:
            ### put a zero in the first element to encourage a negative leading coeff.
            _peaks = zeros(n_peak + 1)
            _deltas = zeros(n_peak + 1)
            _peaks[1:] = peaks[:n_peak]
            _deltas[1:] = deltas[:n_peak]
            p6 = util.poly_fit(_peaks * defaults['dt'], _deltas, 6)
        
        figure(620)
        ax = subplot(311)
        ylabel('Gage mmHG')
        plot(arange(len(bpf)) * defaults['dt'], low_pass_gage)
        plot(arange(len(bpf)) * defaults['dt'], low_low_pass_gage)

        subplot(313, sharex=ax)
        ylabel('Bandpass mmHG')
        plot(arange(len(bpf)) * defaults['dt'], bpf)
        plot(peaks * defaults['dt'], bpf[peaks], 'ro')
        plot(troughs * defaults['dt'], bpf[troughs], 'bo')
        subplot(312, sharex=ax)
        ylabel('Deltas mmHG')
        xlabel('Time Seconds')
        plot(peaks  * defaults['dt'], deltas)
        plot(peaks[:n_peak] * defaults['dt'], deltas[:n_peak], 'bd')
        ylim(0, 6)
        p5 = util.poly_der(p6)
        # map_time = util.find_zero(p5, hills[MAP_ii][1] * defaults['dt'])
        assert n_peak <= len(peaks), 'n_peaks > len(peaks)'
        t = arange(peaks[0] * defaults['dt'], peaks[n_peak - 1] * defaults['dt'], .1)
        y = util.poly_eval(p6, t)
        map_time = t[argmax(y)]
        plot([map_time], [max(y)], 'ro')
        # t = arange(0, 3 * map_time, .1)
        # y = util.poly_eval(p6, t)
        plot(t, y, 'r-')
        map_idx = int(map_time / defaults['dt'])
        MAP6 = low_low_pass_gage[map_idx]

        sbp_target = .55 * util.poly_eval(p6, map_time)
        dbp_target = .85 * util.poly_eval(p6, map_time)
        plot([map_time, map_time], [0, util.poly_eval(p6, map_time)], 'r--')
        plot([0, t[-1]], [dbp_target, dbp_target], 'r--')
        plot([0, t[-1]], [sbp_target, sbp_target], 'r--')
        
        #### find SBP time
        t = arange(map_time, 0, -.01) ### time going backwards from MAP
        pt = util.poly_eval(p6, t) - sbp_target
        sbp_time = t[where(pt < 0)[0][0]]

        #### find DBP time
        t = arange(map_time, 30 * map_time, .01)
        pt = util.poly_eval(p6, t) - dbp_target
        dbp_time = t[where(pt < 0)[0][0]]
        
        plot([dbp_time, dbp_time], [0, dbp_target], 'r--')
        plot([sbp_time, sbp_time], [0, sbp_target], 'r--')

        assert sbp_time < map_time, 'sbp_time = %s > %s = MAP' % (sbp_time, map_time)
        assert map_time < dbp_time, 'dbp_time = %s < %s = MAP' % (dbp_time, map_time)
            
        sbp_idx = int(sbp_time / defaults['dt'])
        dbp_idx = int(dbp_time / defaults['dt'])

        figure(124)
        plot(peaks[:n_peak] * defaults['dt'], deltas[:n_peak])
        plot([map_time], [util.poly_eval(p6, map_time)], 'go')
        plot([dbp_time], [util.poly_eval(p6, dbp_time)], 'bo')
        plot([sbp_time], [util.poly_eval(p6, sbp_time)], 'ro')
        # plot(arange(0, peaks[n_peak] * defaults['dt'], 1), util.poly_eval(p6, arange(0, peaks[n_peak] * defaults['dt'], 1)))
        plot([0, 25], [dbp_target, dbp_target], 'g--')
        plot([0, 25], [sbp_target, sbp_target], 'r--')

        __SBP = low_low_pass_gage[sbp_idx]
        __DBP = low_low_pass_gage[dbp_idx]
        figure(620)
        subplot(311)
        plot([sbp_idx * defaults['dt'], sbp_idx * defaults['dt']],
             [0, __SBP], 'r--')
        plot([dbp_idx * defaults['dt'], dbp_idx * defaults['dt']],
             [0, __DBP], 'r--')
        plot([0, sbp_time], [low_low_pass_gage[sbp_idx], low_low_pass_gage[sbp_idx]], 'r--')
        plot([0, dbp_time], [low_low_pass_gage[dbp_idx], low_low_pass_gage[dbp_idx]], 'r--')
        figure(620); subplot(311); title('%d/%d'  % (__SBP, __DBP))
        d = os.path.split(filename)[0]
        d_bp_fn = os.path.join(d, 'derived_BP.png')
        savefig(d_bp_fn)

        if False:
            subplot(312)
            plot([sbp_idx * defaults['dt'], sbp_idx * defaults['dt']],
                 [-3, 3])
            plot([dbp_idx * defaults['dt'], dbp_idx * defaults['dt']],
                 [-3, 3])
        # assert abs(util.poly_eval(p6, sbp_time) - sbp_target) < 1e-6

    ii = util.edit_deltas(delta_vs)
    ii = range(len(delta_vs))
    delta_vs = [delta_vs[i] for i in ii]
    cuff_pressures = [cuff_pressures[i] for i in ii]
    cuff_pressures = array(cuff_pressures)
    if MAP is None:
        MAP = MAP6
        SBP = __SBP
        DBP = __DBP
    transmuralP = MAP - cuff_pressures 

    __deltas, __MAP, __SBP, __DBP, HR = util.get_edited_deltas(low_pass_gage, bpf, PEAK_HEIGHT)
    if SBP is None:
        SBP = __SBP
    if DBP is None:
        DBP = __DBP
    assert SBP > DBP, '%.2f = SBP <= DBP = %.2f' % (SBP, DBP)
    arterial_compliance = abs(array(delta_vs) / (SBP - DBP) )
    figure(7)
    plot(transmuralP, arterial_compliance)
    
    return arterial_compliance, transmuralP, SBP, DBP, MAP, HR, cba

class Empty:
    pass

def find_offset_index(d1, d2):
    '''
    return index where data corrlates most.
    '''
    corr = []
    if len(d1) > len(d2):
        raise ValueError('first argument should be shorter than second argument')
        d1, d2 = d2, d1 ## make first one shorter

    d2 = ravel([d2, d2])
    N = min([len(d1), len(d2)])
    v1 = d1 / linalg.norm(d1)
    for offset in range(N):
        v2 = d2[offset:offset + N]
        v2 /= linalg.norm(v2)
        corr.append(dot(v1, v2))
    return argmax(corr)

def unpickle(pickle_file):
    '''
    Restore a saved pressure data file
    '''
    ucontrol = Empty()
    dat = pickle.load(pickle_file)
    ucontrol.normal = dat['normal']
    ucontrol.normal_temp = dat['normal_temp']
    ucontrol.normal_pressure = dat['normal_pressure']

    ucontrol.hyper = dat['hyper']
    ucontrol.hyper_temp = dat['hyper_temp']
    ucontrol.hyper_pressure = dat['hyper_pressure']
    return ucontrol

def main(filename):
    minn_score = 'NA'
    directory, fn = os.path.split(filename)
    notes_fn = os.path.join(directory, 'Notes.txt')
    if os.path.exists(notes_fn):
        minn_notes = open(notes_fn).readlines()
        for line in minn_notes:
            keyval = line.upper().split()
            if len(keyval) != 2:
                continue
            key, val = line.upper().split()
            if key == 'SCORE':
                minn_score = '%s.0%%' % (val)
                break
    figure(7); clf()
    title("Arterial compliance vs transmural pressure\n%s" % directory)
    ucontrol = unpickle(open(filename))
    
    norm = ucontrol.normal
    amb_temp_n = ucontrol.normal_temp
    amb_temp_n = 21
    amb_pressure_n  = ucontrol.normal_pressure
    amb_pressure_n = 728.

    hype = ucontrol.hyper
    amb_temp_h = ucontrol.hyper_temp
    amb_temp_h = amb_temp_h
    amb_pressure_h  = ucontrol.hyper_pressure
    amb_pressure_h  = amb_pressure_n

    n_skip = 750

    gage_n = array([l[1] for l in norm])  ## pressure in mmhg
    lpg_n = util.filter(gage_n - gage_n[0], LP_TAPS) + gage_n[0]
    llpg_n = util.filter(gage_n - gage_n[0], LLP_TAPS) + gage_n[0]

    gage_h = array([l[1] for l in hype])  ## pressure in mmhg
    lpg_h = util.filter(gage_h - gage_h[0], LP_TAPS) + gage_h[0]
    llpg_h = util.filter(gage_h - gage_h[0], LLP_TAPS) + gage_h[0]

    flow_n = util.filter(array([l[2] for l in norm]), DELAY_TAPS)
    flow_h = util.filter(array([l[2] for l in hype]), DELAY_TAPS)
    gage_n = util.filter(gage_n, DELAY_TAPS)
    gage_h = util.filter(gage_h, DELAY_TAPS)

    gage_n = gage_n[n_skip:]
    gage_h = gage_h[n_skip:]
    lpg_n = lpg_n[n_skip:]

    lpg_h = lpg_h[n_skip:]
    llpg_n = llpg_n[n_skip:]
    llpg_h = llpg_h[n_skip:]
    flow_n = flow_n[n_skip:]
    flow_h = flow_h[n_skip:]

    
    ac1, tp1, SBP, DBP, MAP, HR, cba = get_arterial_compliance(flow_n, llpg_n, lpg_n, amb_temp_n, amb_pressure_n, cba=None)
    print os.path.split(filename)[0], '\t%.0f\t%.0f' % (SBP, DBP)
    
usage = Exception("python arterial_compliance.py <filename.dat>")
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            close('all')
            try:
                main(filename)
            except KeyboardInterrupt:
                raise
            except Exception, e:
                print os.path.split(filename)[0], '\t NA \t NA\t', e
                # if raw_input('...').lower() == 'r':
                #     raise
    else:
        raise usage
# show()
