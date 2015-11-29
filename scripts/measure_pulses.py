import sys
from uControl import *
import util
import glob

def plot_gage_and_flow(hirate):
    pass
def plot_hirate(hirate, color):
    dt = 0.004
    n_tap = 100
    fmax = 10 ## Hz
    lp_taps = util.get_lowpass_taps(fmax, dt, n_tap)
    delay_taps = zeros(defaults['n_tap'])
    delay_taps[defaults['n_tap'] // 2] = 1
    
    lpd = util.filter(hirate[:,1] - hirate[0, 1], lp_taps) + hirate[0, 1]

    ax = pylab.subplot(211)
    times = hirate[:,0]
    pylab.plot(times, lpd)
    peaks, troughs = util.find_peaks_and_troughs(lpd, eps=.1, edit=False)
    if peaks[0] < troughs[0]:
        peaks = peaks[1:]
    if peaks[-1] < troughs[-1]:
        troughs = troughs[:-1]
    pylab.plot(times[peaks], lpd[peaks], 'ro')
    pylab.plot(times[troughs], lpd[troughs], 'bo')
    deltas = lpd[peaks] - lpd[troughs]
    print std(deltas)
    pylab.subplot(212)
    pylab.plot(lpd[troughs], deltas)
    
def test(filename):
=======
    pylab.ylabel('Low Pass mmHG')
    pylab.xlabel('Time')
    times = hirate[:,0] / 1000.
    lt =  '%s-' % color
    pylab.plot(times, lpd, lt)
    peaks, troughs = util.find_peaks_and_troughs(lpd, eps=.05, edit=False)
    if peaks[0] < troughs[0]:
        peaks = peaks[1:]
    if troughs[-1] > peaks[-1]:
        troughs = troughs[:-1]
    pylab.plot(times[peaks], lpd[peaks], 'ro')
    pylab.plot(times[troughs], lpd[troughs], 'bo')
    deltas_l = (lpd[peaks] - lpd[troughs])[:-1]
    deltas_r = lpd[peaks[:-1]] - lpd[troughs[1:]]
    deltas = (deltas_r + deltas_l) / 2.
    peaks = (peaks[1:] + peaks[:-1])/2
    troughs = (troughs[1:] + troughs[:-1])/2
    pylab.subplot(212)
    pylab.ylabel('Cuff Compliance mmHG')
    pylab.xlabel('cuff pressure mmHG')
    dV = 2 ## mL
    pylab.plot(lpd[troughs], dV/deltas, lt)

    
def test(basename, port=None):
>>>>>>> 50863957b4bae477e73a3b4163108e43922d53f7
    print 'here we go'
    uc = uControl(port=port)
    try:
        print 'uc.cuff_pressure', uc.cuff_pressure
        print 'maintain(100, 130, 3)'
        print 'pump to 100 mmHG'
        uc.inflate(130, lambda *args:None)
        uc.deflate(100)
        uc.send_cmd(pump_state=False, valve_state=False)
        # time.sleep(30)
        uc.record(True)
        print "recording..."
        start = time.time()
        # uc.deflate(3)
        try:
            while uc.cuff_pressure > 2:
                print 'uc.cuff_pressure', uc.cuff_pressure
                for i in range(10):
                    serial_interact()
        except KeyboardInterrupt:
            pass
        uc.record(False)
        
        print 'len(uc.hirate)', len(uc.hirate)
        hirate = array(uc.hirate)
        if len(uc.hirate) > 0:
<<<<<<< HEAD
            pfn = filename
=======
            pfn = '%s%03d.pkl' % (basename, len(glob.glob('%s*.pkl' % basename)))
>>>>>>> 50863957b4bae477e73a3b4163108e43922d53f7
            pickle.dump(hirate, open(pfn, 'w'))
            print 'wrote', pfn
            # plot_hirate(hirate)
        print 'done'
    finally:
        # uc.deflate(50)
        send_cmd(pump_rate=False, valve=True)
        time.sleep(2)
        send_cmd(pump_rate=False, valve=False, interval=0)
    pylab.show()

# if True:
if False:
<<<<<<< HEAD
    if len(sys.argv) > 1:
        pfn = sys.argv[1]
    else:
        pfn = 'bartendro_test_002.pkl'
    hirate = pickle.load(open(pfn))
    plot_hirate(hirate)
    pylab.show()
    here
if __name__ == '__main__':
    try:
        command = sys.argv[1]
        filename = sys.argv[2]
    except:
        raise ValueError("python measure_pulses.py <meas|plot> <filename>")
    if command == 'meas':
        test(filename)
    else:
        plot_hirate(pickle.load(open(filename)))
=======
    # hirate = pickle.load(open('bartendro_test_002.pkl'))
    ids = [4]
    for id in ids:
        fn = "air_ccl_%03d.pkl" % id
        plot_hirate(pickle.load(open(fn)), 'g')
    pylab.show()
    for id in ids:
        fn = "liq_ccl_%03d.pkl" % id
        plot_hirate(pickle.load(open(fn)), 'b')
    here
    plot_hirate(pickle.load(open('air_tight_000.pkl')))
    plot_hirate(pickle.load(open('air_tight_001.pkl')))
    plot_hirate(pickle.load(open('air_tight_002.pkl')))
    
    plot_hirate(pickle.load(open('liq_tight_000.pkl')))
    plot_hirate(pickle.load(open('liq_tight_001.pkl')))
    plot_hirate(pickle.load(open('liq_tight_002.pkl')))

    plot_hirate(pickle.load(open('air_med_000.pkl')))
    plot_hirate(pickle.load(open('air_med_001.pkl')))
    plot_hirate(pickle.load(open('air_med_002.pkl')))

    plot_hirate(pickle.load(open('liq_med_000.pkl')))
    plot_hirate(pickle.load(open('liq_med_001.pkl')))
    plot_hirate(pickle.load(open('liq_med_002.pkl')))


    pylab.show()
    here
if __name__ == '__main__':
    import sys
    usage = ValueError("python measure_pulses.py basename [port=None, n_trail=1]")
    try:
        if len(sys.argv) < 2:
            raise usage
        basename = sys.argv[1]
        if len(sys.argv) > 2:
            port = sys.argv[2]
        else:
            port = None
        if len(sys.argv) > 3:
            n_trial = int(sys.argv[3])
        else: 
            n_trial = 1
        for i in range(n_trial):
            test(basename, port)

    except ValueError:
        raise usage
>>>>>>> 50863957b4bae477e73a3b4163108e43922d53f7
