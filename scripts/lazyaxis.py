from pylab import *

class LazyAxes:
    def __init__(self, names):
        self.axes = {}
        for name in names:
            self.axes[name] = LazyAxis(name)
    def __getitem__(self, name):
        out = self.axes[name]
        return out
    def __contains__(self, name):
        return name in self.axes
    def clear_all(self):
        for name in self.axes:
            self.axes[name].cla()
class LazyAxis:
    '''
    Delay calling all methods of a class until involked by owner
    '''
    def __init__(self, name):
        self.cla()
        self.name = name
    def cla(self, *args, **kw):
        self.plots = []
        self.texts = []
        self.fills = []
        self.xlabel_dat = None
        self.ylabel_dat = None
        self.title_dat = None
        self.xlim_args = [[], {}]
        self.ylim_args = [[], {}]
    def plot(self, *args, **kw):
        self.plots.append([args, kw])
    def fill_between(self, *args, **kw):
        self.fills.append([args, kw])
    def xlabel(self, *args, **kw):
        self.xlabel_dat = (args, kw)
    def ylabel(self, *args, **kw):
        self.ylabel_dat = (args, kw)
    def title(self, *args, **kw):
        self.title_dat = (args, kw)
    def text(self, *args, **kw):
        self.texts.append([args, kw])
    def xlim(self, *args, **kw):
        self.xlim_args = [args, kw]
    def ylim(self, *args, **kw):
        self.ylim_args = [args, kw]        
    def draw_on(self, ax):
        ax.clear()
        for args, kw in self.fills:
            ax.fill_between(*args, **kw)
        for args, kw in self.plots:
            ax.plot(*args, **kw)
        for args, kw in self.texts:
            ax.text(*args, **kw)
        if self.xlabel_dat:
            ax.set_xlabel(*self.xlabel_dat[0], **self.xlabel_dat[1])
        if self.ylabel_dat:
            ax.set_ylabel(*self.ylabel_dat[0], **self.ylabel_dat[1])
        if self.title_dat:
            pass
            # ax.set_title(*self.title_dat[0], **self.title_dat[1])
        # ax.text(.5, .5, self.name, transform=ax.transAxes)
        ax.set_xlim(*self.xlim_args[0], **self.xlim_args[1])
        ax.set_ylim(*self.ylim_args[0], **self.ylim_args[1])

def __LazyAxis__test__():        
    la = LazyAxis('test')
    la.plot(range(10))
    la.fill_between(range(10), range(0, 20, 2), range(10))
    la.xlabel('x')
    la.ylabel('y')
    la.title('title')
    fig = figure()              
    ax = fig.add_subplot(111)
    la.draw_on(ax)

def __LazyAxes__test__():
    la = LazyAxes('testing 1 2 3'.split())
    assert '1' in la
    assert isinstance(la['1'], LazyAxis)

import pretest, lazyaxis
pretest.pretest('lazyaxis') 
