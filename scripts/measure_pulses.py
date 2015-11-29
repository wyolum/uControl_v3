import sys
from uControl import *
import util

def plot_gage_and_flow(hirate):
    pass
def plot_hirate(hirate):
    dt = 0.004
    n_tap = 100
    lp_taps = util.get_lowpass_taps(4, dt, n_tap)
    
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
    print 'here we go'
    uc = uControl()
    try:
        print 'uc.cuff_pressure', uc.cuff_pressure
        print 'maintain(100, 130, 3)'
        print 'pump to 100 mmHG'
        # uc.maintain(120, 130, 10)
        uc.record(True)
        start = time.time()
        print "recording..."
        try:
            while 1:
                print 'uc.cuff_pressure', uc.cuff_pressure
                serial_interact()
        except KeyboardInterrupt:
            pass
        uc.record(False)
        
        print 'len(uc.hirate)', len(uc.hirate)
        hirate = array(uc.hirate)
        if len(uc.hirate) > 0:
            pfn = filename
            pickle.dump(hirate, open(pfn, 'w'))
            print 'wrote', pfn
            plot_hirate(hirate)
        print 'done'
    finally:
        # uc.deflate(50)
        send_cmd(pump_rate=False, valve=True)
        time.sleep(2)
        send_cmd(pump_rate=False, valve=False, interval=0)
    pylab.show()

if False:
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
