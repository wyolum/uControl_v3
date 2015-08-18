import sys
import pickle
import matplotlib;matplotlib.use('TkAgg')
import time

from constants import *
import util
import numpy
import scipy.interpolate.interpolate as interp
import pylab

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from uControl import uControl
from Tkinter import *
import Tkinter, tkFileDialog
import threading
from lazyaxis import LazyAxes

## Filter taps
LP_TAPS = util.get_lowpass_taps(defaults['high_cuttoff_hz'], 
                                defaults['dt'],
                                defaults['n_tap'])
LLP_TAPS = util.get_lowpass_taps(defaults['low_cuttoff_hz'], 
                                 defaults['dt'],
                                 defaults['n_tap'])


def unpickle(pickle_file):
    '''
    Restore a saved pressure data file
    '''
    dat = pickle.load(pickle_file)
    ucontrol.normal = dat['normal']
    ucontrol.normal_temp = dat['normal_temp']
    ucontrol.normal_pressure = dat['normal_pressure']

    ucontrol.hyper = dat['hyper']
    ucontrol.hyper_temp = dat['hyper_temp']
    ucontrol.hyper_pressure = dat['hyper_pressure']

class Runner(threading.Thread):
    '''
    This thread runs uControl so that GUI can remain resonsive during execution.
    '''
    def __init__(self):
        threading.Thread.__init__(self)
        self.abort = False
        self.state = 0
    def run(self):
        print 'Normal run!'
        self.do_run(hold=0)
        ucontrol.normal = ucontrol.hirate
        ucontrol.normal_temp = ucontrol.amb_temp
        ucontrol.normal_pressure = ucontrol.amb_pressure

        print 'Hyper run!'
        self.do_run(hold=defaults['hold_sec'])
        # self.do_run(hold=0); print 'TODO: revert hold time.  Testing only'
        ucontrol.hyper = ucontrol.hirate
        ucontrol.hyper_temp = ucontrol.amb_temp
        ucontrol.hyper_pressure = ucontrol.amb_pressure
        self.state = 5
    def abort_now(self):
        '''
        Used to feed back information to uControl when the user quits in the middle of a run.  Return true if the
        use has aborted.
        '''
        return self.abort

    def do_run(self, hold):
        '''
        inflate -- hold -- release
        state attribute is used to update GUI
        state 
        0 -- initialized
        1 -- inflation
        2 -- hold
        3 -- deflate
        4 -- run complete
        5 -- plotting
        '''
        ucontrol.hirate = []
        self.state = 1
        ucontrol.inflate(defaults['max_pressure'], self.abort_now)
        self.state = 2
        ucontrol.maintain(defaults['min_hold_pressure'], defaults['max_pressure'], hold, self.abort_now)
        self.state = 3
        ucontrol.amb_pressure = None
        ucontrol.amb_temp = None
        while ucontrol.amb_temp is None:
            ucontrol.send_cmd(amb_pressure=1, amb_temp=1)
            ucontrol.delay(.1)
        ucontrol.record(True)
        ucontrol.deflate(15)
        ucontrol.amb_pressure = None
        ucontrol.amb_temp = None
        while ucontrol.amb_temp is None:
            ucontrol.send_cmd(amb_pressure=1, amb_temp=1)
            ucontrol.delay(.1)
        self.state = 4
        ucontrol.record(False)

runner = Runner()
def run():
    '''
    Called when "go" button is clicked
    '''
    ax.clear()
    canvas.show()
    global runner
    runner = Runner()
    runner.start()

def abort():
    '''
    Called when "abort" button is pressed.
    '''
    runner.abort = True
    if runner.isAlive():
        runner.join()
        runner.abort = False
    
class ToggleButton(Button):
    '''
    Button that toggles between two states and functions.
    '''
    def __init__(self, parent, texts, state, onTrue, onFalse):
        Button.__init__(self, parent, text=texts[0], background='green', activebackground='green', 
                        command=self)
        self.texts = texts
        self.init_state = state
        self.state = state
        self.onTrue = onTrue
        self.onFalse = onFalse

    def onPress(self, state=None):
        if state is not None:
            self.state = state
        else:
            self.state = not self.state
        if self.state:
            self.config(text=self.texts[1], background='red', activebackground='red')
            out = self.onTrue()
        else:
            self.config(text=self.texts[0], background='green', activebackground='green')
            out = self.onFalse()
        return out

    def reset(self):
        self.state = self.init_state
        if self.state:
            self.config(text=self.texts[1], background='red', activebackground='red')
        else:
            self.config(text=self.texts[0], background='green', activebackground='green')
        
    def __call__(self):
        return self.onPress()

def alert(info):
    '''
    alert dialog box popup
    '''
    import tkMessageBox
    tkMessageBox.showinfo(message=info)

file_opt={}
def file_open():
    '''
    Open a data capture file
    Returns an opened file in read mode.
    '''
    out = tkFileDialog.askopenfile(mode='r', **file_opt)
    try:
        unpickle(out)
        ax.clear()
        runner.state = 5
    except Exception, e:
        alert('File format not recognized: %s\n    %s' % (out.name, e))
    return out

def file_save():
    '''
    Save a data capture file
    '''
    out = tkFileDialog.asksaveasfile(mode='w', **file_opt)
    pickle.dump({'normal':ucontrol.normal, 
                 'normal_temp':ucontrol.normal_temp,
                 'normal_pressure':ucontrol.normal_pressure,
                 'hyper':ucontrol.hyper,
                 'hyper_temp':ucontrol.normal_temp,
                 'hyper_pressure':ucontrol.normal_pressure}, out)
    out.close()


### start building GUI
root = Tk()
root.title("Cordex EnDys Score")
menubar = Menu(root)
root.config(menu=menubar)
fileMenu = Menu(menubar)
fileMenu.add_command(label="Open", command=file_open)
fileMenu.add_command(label="Save", command=file_save)
fileMenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=fileMenu)

################################################################################
# 
#                this is the plotting code
fig = Figure(figsize=(5,4), dpi=100)
ax = fig.add_subplot(111)
# ax.set_xlim(0, 30)
ax.set_xlabel('Trans-Mural Pressure mm Hg')
# ax.set_ylim(0, 250)
ax.set_ylabel('Arterial Compliance')
fig.subplots_adjust(left=.15, bottom=.125)
# a tk.DrawingArea

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

toolbar_frame = Tkinter.Frame(root)
toolbar = NavigationToolbar2TkAgg(canvas, toolbar_frame)
toolbar.pack(side=LEFT, fill=X)
toolbar_frame.pack(side=TOP, fill=X)
toolbar.update()
canvas.show()
################################################################################

button = ToggleButton(root, ['Go', 'Abort'], False, run, abort)
button.pack()

pressure_label = Label(root, text=' 0 mm Hg')
pressure_label.pack(side=LEFT)
state_label = Label(root, text='')
state_label.pack(side=LEFT)

state_strs = ['Ready', 'Inflating', 'Holding', 'Deflating', 'Normal Done', 'Complete']

def plot(x, y=None, ltype=''):
    if y is None:
        y = x
        x = range(len(y))
    ax.plot(x, y, ltype)
    canvas.show()
def fill(x, y):
    ax.fill(x, y, alpha=.3)
    canvas.show()
    
def flow_of_gage(gage):
    ### ALL best fit [ -6.58671169e+00   8.19409655e-02   7.47864630e-04]
    c, b, a = [ -6.58671169e+00,   8.19409655e-02,   7.47864630e-04]
    c, b, a = numpy.array([ 0.,         -0.02387275,  0.00170359]) ### corrected
    c, b, a = numpy.array([ 0.,         -0.01285073,  0.00168245])
    return (-b + numpy.sqrt(b ** 2 - 4 * a * (c - gage))) / (2 * a)

def get_arterial_compliance(time, flow, low_low_pass_data, low_pass_data, normal_map=None):
    wvol = numpy.cumsum(flow) * defaults['dt']  ### measured
    wvol = numpy.cumsum(flow_of_gage(low_low_pass_data))  * defaults['dt']         ### best fit
    # plot(low_low_pass_data)
    
    lo = low_low_pass_data
    hi = low_pass_data
    bpf = hi - lo
    v_of_p = interp.interp1d(lo[::-1], wvol[::-1], bounds_error=False)
    peaks, troughs = util.find_peaks_and_troughs(bpf, PEAK_HEIGHT, edit=False)
    if peaks[0] < troughs[0]: # peak follows trough
        peaks = peaks[1:]
    if troughs[-1] > peaks[-1]: # peak follows trough
        troughs = troughs[:-1]
    pylab.figure(1)
    pylab.plot(bpf)
    pylab.plot(peaks, bpf[peaks])
    pylab.plot(troughs, bpf[troughs])

    hills = []
    for trough, peak in zip(troughs, peaks): ## filter loong pulses
        if (peak - trough) * defaults['dt'] < MAX_PULSE:
            hills.append((trough, peak))
    assert len(peaks) == len(troughs)
    hills = numpy.array(hills)
    troughs = hills[:,0]
    peaks = hills[:,1]

    deltas = []
    cuff_pressures = []
    for p, t in hills:
        cuff_pressure = (lo[p] + lo[t])/2.
        p_t = hi[t]
        p_p = hi[p]
        deltav_p = v_of_p(p_p) - wvol[p]
        deltav_t = v_of_p(p_t) - wvol[t]
        delta_v = deltav_p - deltav_t
        deltas.append(delta_v)
        cuff_pressures.append(cuff_pressure)
    i = numpy.argmax(deltas)
    MAP = lo[hills[i][1]]

    ### compute map6
    pylab.figure(6)
    x = numpy.arange(0, 180)
    pylab.plot(x, v_of_p(x))
    pylab.plot(lo[::-1], wvol[::-1], 'o')
    pylab.figure(5)
    pylab.title("Deltas?")
    deltas = bpf[peaks] - bpf[troughs]
    MAP_ii = numpy.argmax(deltas)
    MAP_i = hills[MAP_ii][1]
    MAP = low_low_pass_data[MAP_i]
    pylab.plot([h[1] for h in hills], deltas, 'b-')
    pylab.plot([hills[MAP_ii][1]], [bpf[hills[MAP_ii][1]] - bpf[hills[MAP_ii][0]]], 'rx')
    p6 = util.poly_fit(troughs / 1000., deltas, 8)
    p5 = util.poly_der(p6)
    
    pylab.figure(2)
    pylab.plot(peaks * defaults['dt'], deltas, 'o')
    pylab.plot(peaks * defaults['dt'], util.poly_eval(p6, peaks / 1000.))
    pylab.title("Peaks with 6th order poly fit")
    floor = interp.interp1d(troughs * defaults['dt'], bpf[troughs], bounds_error=False)
    x = numpy.arange(len(bpf)) * defaults['dt']
    pylab.plot(x, bpf - floor(x))
    pylab.xlabel("Time (seconds)")
    pylab.ylabel("Band Pass Pressure (mm Hg)")
    pylab.legend(["    $\Delta$",
                  "    6th order poly",
                  "    pressure data"])
    pylab.ylim(0, 3)
    # pylab.savefig("map6.png")
    # here
    pylab.figure(3)
    pylab.plot(low_low_pass_data[troughs], deltas, 'o')
    pylab.plot(low_low_pass_data[troughs], util.poly_eval(p6, troughs / 1000.))
    pylab.title("Sixth order poly fit: PEAKS")
    MAP6 = low_low_pass_data[int(util.find_zero(p5, hills[MAP_ii][1] / 1000.) * 1000)]
    print MAP6, 'MAP6', MAP, 'MAP'
    # pylab.figure(4)
    # pylab.plot(low_low_pass_data)
    # pylab.title("low low pass data")
    #####

    ii = util.edit_deltas(deltas)
    deltas = [deltas[i] for i in ii]
    cuff_pressures = [cuff_pressures[i] for i in ii]
    cuff_pressures = numpy.array(cuff_pressures)
    transmuralP = MAP - cuff_pressures ## orig
    # transmuralP = MAP6 - cuff_pressures
    # transmuralP = 120 - cuff_pressures
    thresh = .15
    ## plot(bpf)

    __deltas, __MAP, SBP, DBP, HR = util.get_edited_deltas(lo, bpf, thresh)
    arterial_compliance = numpy.array(deltas) / (SBP - DBP)
    pylab.figure(7)
    pylab.plot(transmuralP, arterial_compliance)
    pylab.title("Arterial Compliance vs TMP")
    return arterial_compliance, transmuralP, SBP, DBP, HR

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
    P_s = 1013. # mbar
    T_s = 293.15  # K
    if amb_p is None:
        amb_p = P_s
    P_true = amb_p + gage_p
    T_true = amb_t + 273.15 # K
    ambient_correction_factor = (P_s * T_true) / (T_s * P_true)
    return flow * ambient_correction_factor

def update():
    '''
    Update the GUI with current status.
    '''
    # print 'UPDATE!'
    try:
        pressure_label.config(text='%.0f mm Hg' % listener.last_mpid.cuff)
    except:
        pass
    if runner:
        state_label.config(text=state_strs[runner.state])
        if runner.state == 5: ## complete
            runner.state = 0  ## back to ready
            try:
                button.config(text=button.texts[0], background='green', activebackground='green', state=NORMAL)
                button.state = False
                areas = []
                curves = []
                abort = False
                for i, hirate in enumerate([ucontrol.normal, ucontrol.hyper]):
                    hirate = hirate[100:]
                    x = numpy.array([l[0] for l in hirate]) / 1000. ## time in seconds
                    pressure = numpy.array([l[1] for l in hirate])  ## pressure in mmhg
                    flow = numpy.array([l[2] for l in hirate])
                    flow = flow_correction(flow, 
                                           pressure, 
                                           ucontrol.normal_pressure, 
                                           ucontrol.normal_temp)
                    ## clean up flow data
                    i_s = numpy.where(numpy.greater(flow, 1000))[0]
                    if len(i_s) > 0:
                        flow[i_s] = flow[i_s[0] - 1]
                    flow = util.filter(flow - flow[0], LLP_TAPS) + flow[0]

                    x -= x[0]
                    lpd = util.filter(pressure - pressure[0], LP_TAPS) + pressure[0]
                    llpd = util.filter(pressure - pressure[0], LLP_TAPS) + pressure[0]
                    y = lpd - llpd
                    try:
                        ## deltas, MAP, SBP, DBP, HR
                        # deltas, MAP, SBP, DBP, HR = util.get_edited_deltas(pressure, y, .001)
                        arterial_compliance, trans_pressure, SBP, DBP, HR = get_arterial_compliance(x, flow, llpd, lpd)
                        
                        ### keep only the positive transmural region
                        arterial_compliance = arterial_compliance[trans_pressure > 0]
                        trans_pressure = trans_pressure[trans_pressure > 0]
                        if i == 1:
                            # print MAP, SBP, DBP, HR
                            ax.text(max(trans_pressure) * .7, 
                                    max(arterial_compliance) * .7, 'HR: %s\nBP: %s/%s' % (HR, int(SBP), int(DBP)))
                        plot(trans_pressure, arterial_compliance, '-o')
                        curves.append([trans_pressure, arterial_compliance])
                        areas.append(util.integrate(trans_pressure, arterial_compliance))
                        print 'AREA:', -areas[-1]
                                     
                    except ValueError, e:
                        alert("No delta's found in dataset\n    %s" % e)
                        abort = True
                if not abort:
                    xs = list(curves[0][0])
                    xs.extend(curves[1][0][::-1])
                    ys = list(curves[0][1])
                    ys.extend(curves[1][1][::-1])
                    fill(xs, ys)
                    pylab.show()
                    
            except ValueError, e:
                alert('Problem with data set\n    %s' % str(e))
                abort()
        

    else:
        state_label.config(text=state_strs[0])
    root.after(100, update)

class Listener:
    '''
    Handle messages from uControl
    '''
    def mpid_cb(self, ucontrol, pkt):
        self.last_mpid = pkt
        # ucontrol.abort()
    def lpid_cb(self, ucontro, pkt):
        self.last_lpid = pkt
    def status_cb(self, ucontrol, pkt):
        self.last_status = pkt
    def short_cb(self, ucontrol, pkt):
        self.last_short = pkt

class Empty:
    pass

listener = Listener()
try:
    ucontrol = uControl(listener)
except:
    ucontrol = Empty()
def main(filename=None):
    if filename:
        unpickle(open(filename))
        runner.state = 5
        update()
    else:
        root.after(100, update)
        root.mainloop()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None
    main(filename)
