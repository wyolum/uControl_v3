from uControl import *
from pylab import *
import util

def load(fn):
    data = pickle.load(open(fn))
    try:
        out = data['hirate']
    except ValueError:
        out = data
    return out
    

def plot_hirate(hirate):
    times = hirate[:,0]
    gage = hirate[:,1]
    flow = hirate[:,2]

    figure(1)
    ax = pylab.subplot(211)
    ylabel('Gage mmHG')
    pylab.plot(times, gage)
    pylab.subplot(212)
    xlabel('Time sec.')
    ylabel('Flow')
    pylab.plot(times, flow)
    
    figure(2) ## plot high pass data
    lp_taps = util.get_lowpass_taps(.5, dt=.004, n=100)
    hpd = util.filter(gage - gage[0], lp_taps) + gage[0]
    plot(gage, gage - hpd)

if __name__ == '__main__':
    import sys
    usage = 'python plot_uc.py [ucontrol.pkl, ...]'
    if len(sys.argv) > 1:
        for fn in sys.argv[1:]:
            # fn = sys.argv[1]
            hirate = load(fn)
            plot_hirate(hirate)
        show()
    else:
        raise Exception(usage)
    
