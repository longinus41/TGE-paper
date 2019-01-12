#author : Athrun Arthur

import os
import json
import matplotlib.pyplot as plt
import pickle
import numpy as np

def make_standalone(fig):
    '''This is used to wrap a fig with tex headers
    '''
    header = '\\documentclass[border=3mm]{standalone}\n'
    header += '\\usepackage{pgfplots}\n'
    header += '\\pgfplotsset{compat=newest}\n'
    header += '\\pagestyle{empty}\n'
    header += '\\begin{document}\n'
    header += '\\begin{tikzpicture}\n'

    end = '\\end{tikzpicture}\n'
    end += '\\end{document}'

    return header + fig + end

class PlotSet:
    def __init__(self, name):
        self.ps_name = name
        self.nl = '&%&'

        self.items = []

    def name(self):
        return self.ps_name

    def set_one(self, item):
        self.items.append(str(item))

    def set_two(self, key, value):
        self.items.append(str(key) + ' = ' + str(value))

    def set_list(self, key, value):
        ns = '{'
        for item in value:
            ns += '{' + str(item) + '}, '
        ns += '}'
        self.items.append(str(key) + ' = ' + str(ns))

    def set_dict(self, key, dict):
        ns = '{'
        for k, v in dict.items():
            ns += str(k) + '=' + str(v) + ', '
        ns += '}'
        self.items.append(str(key) + ' = ' + str(ns))


    def __generate_json_str(self):

        res = '\\pgfplotsset{' + self.ps_name + '/.style={%' + self.nl
        for item in self.items:
            res += '\t' +str(item) + ',' + self.nl
        res += '}}'
        return res

    def output_to_fp(self, fp):
        content = ''
        tag = '%content:'
        if os.path.exists(fp):
            content = open(fp).read()
        pses =''
        for line in content.splitlines():
            if not line.startswith(tag):
                continue
            pses = line[len(tag):]
        ps = {}
        if len(pses) != 0:
            ps = json.loads(pses)

        ps[self.ps_name] = self.__generate_json_str()

        ##output to fp
        fh = open(fp, 'w')
        fh.write(tag + json.dumps(ps))
        fh.write('\n')

        for k, v in ps.items():
            s = v.replace(self.nl, '\n')
            fh.write(s)
            fh.write('\n')
        fh.close()


class PlotBase:
    def __init__(self):
        self.hs = '\\begin{axis}'
        self.plotset = None
        self.es = '\\end{axis}\n'
        self.legends = []
        self.plots = []
        self.styles = ''
        self.addplot_sufix = ''
        self.annotations = ''

    def config(self, ps):
        self.plotset = ps

    def append_style(self, style):
        self.styles += style.strip()

    def add_annotation(self, ann):
        self.annotations += ann + '\n'

    def plot_sufix(self, sufix):
        self.addplot_sufix = sufix

    def dump(self):
        rs = ''
        rs += self.hs

        has_ps_style = False
        if (not self.plotset is None) or len(self.styles) != 0:
            has_ps_style = True
        if has_ps_style:
            rs += '['

        if not self.plotset is None:
            rs += self.plotset.name()
            if len(self.styles) != 0:
                rs += ', '
        if len(self.styles) != 0:
            rs += self.styles
        if has_ps_style:
            rs += ']'
        rs += ' \n'

        for p in self.plots:
            rs += p

        if len(self.annotations) != 0:
            rs += self.annotations + '\n'

        if len(self.legends) != 0:
            rs += '\\legend{'
        for l in self.legends :
            rs += l + ','
        if len(self.legends) != 0:
            rs = rs.strip(',') + '}\n'

        rs += self.es
        return rs

class Plot(PlotBase):

    def __init__(self):
        PlotBase.__init__(self)

    def addplot(self, data, xfunc, yfunc, style='', legend=''):
        if len(data) == 0:
            return

        s = '\\addplot '
        if len(style) != 0:
            s += '[ ' + style + ' ]'
        s += ' plot coordinates {\n'
        for d in data:
            s += '(' + str(xfunc(d)) + ', ' + str(yfunc(d)) + ')\n'
        s += '};'

        self.plots.append(s)
        if len(legend) != 0:
            self.legends.append(legend)


class CDFPlot(PlotBase):
    def __init__(self):
        PlotBase.__init__(self)

    def addplot(self, data, style='', legend=''):
        '''@data - should be a data set'''

        if len(data) == 0:
            return

        nd = []
        delta = 100.0 / len(data)
        md = {}
        for d in data:
            if not md.has_key(d):
                md[d] = 0
            md[d] += 1

        nd.append((0, 0))
        last = 0.0
        for k, v in sorted(md.items(), key=lambda d:d[0]):
            last += v * delta
            nd.append((k, last))

        s = '\\addplot '
        if len(style) != 0:
            s += '[ ' + style + ' ]'
        s += ' plot coordinates {\n'
        for d in nd:
            s += '(' + str(d[0]) + ', ' + str(d[1]) + ')\n'
        s += '}'
        if len(self.addplot_sufix) == 0:
            s += self.addplot_sufix
        s+= ';'

        self.plots.append(s)
        if len(legend) != 0:
            self.legends.append(legend)

class PDFPlot(PlotBase):
    def __init__(self):
        PlotBase.__init__(self)

    def addplot(self, data, bins, density, style='', legend=''):
        '''@data - should be a data set'''

        if len(data) == 0:
            return

        td = {}
        for d in range(0, bins + 1):
            td[d] = 0

        delta = 1.0 * max(data)/bins

        self.append_style('ybar,')
        self.append_style('ymode=log,')
        self.append_style('bar width={},'.format(delta))
        self.append_style('log origin=infty,')
        self.append_style('xmin=-{},'.format(delta))
        self.append_style('ytick align=outside,')
        self.append_style('enlargelimits=0,')
        for d in data:
            i = int(round(d/delta))
            td[i] += 1

        nd = []
        for k, v in td.items():
            nd.append((k*delta, 1.0 * v/(delta * len(data))))

        s = '\\addplot '
        if len(style) != 0:
            s += '[ ' + style + ' ]'
        s += ' plot coordinates {\n'
        for d in nd:
            s += '(' + str(d[0]) + ', ' + str(d[1]) + ')\n'
        s += '}'
        if len(self.addplot_sufix) == 0:
            s += self.addplot_sufix
        s+= ';'

        self.plots.append(s)
        if len(legend) != 0:
            self.legends.append(legend)

if __name__ == '__main__':
    p = PDFPlot()

    # import math
    # data = []
    # for line in open('degree.txt', 'r'):
    #     data.append(float(line[0]))
    with open("X_asym_181_s.pkl",'rb') as f:
        X=pickle.load(f)
    data_in=[]
    data_out=[]
    weighted_in=[]
    weighted_out=[]
    # max_data=0
    for i in X:
        if i[0]<1e6:
            data_in.append(i[0])
        if i[1]<1e6:
            data_out.append(i[1])
        if i[2]<2e6:
            weighted_in.append(i[2])
        if i[3]<2e6:
            weighted_out.append(i[3])
        # if i[0]>]max_data:
        #     max_data=i[0]
    # print(max_data)

    p.append_style('ymax=0.0001,')
    p.addplot(data_in, 50, True)
    s = p.dump()
    s = make_standalone(s)
    import os
    if not os.path.exists('tt'):
        os.mkdir('tt')
    open('tt/degree_in.tex', 'w').write(s)

    p_out=PDFPlot()
    p_out.append_style('ymax=0.0001,')
    p_out.addplot(data_out, 50, True)
    s = p_out.dump()
    s = make_standalone(s)
    open('tt/degree_out.tex', 'w').write(s)

    p_win=PDFPlot()
    p_win.append_style('ymax=0.00005,')
    p_win.addplot(weighted_in, 50, True)
    s = p_win.dump()
    s = make_standalone(s)
    open('tt/weighted_in.tex', 'w').write(s)

    p_wout=PDFPlot()
    p_wout.append_style('ymax=0.00005,')
    p_wout.addplot(weighted_out, 50, True)
    s = p_wout.dump()
    s = make_standalone(s)
    open('tt/weighted_out.tex', 'w').write(s)

    # fake_p = PDFPlot()
    # fake_p.append_style('ymax=0.0001,')
    # data = []
    # for line in open('fake_accounts_var.txt', 'r'):
    #     data.append(float(line))

    # fake_p.addplot(data, 15, True);
    # s = fake_p.dump()
    # s = make_standalone(s)
    # import os
    # if not os.path.exists('tt'):
    #     os.mkdir('tt')
    # open('tt/fake_accounts_var.tex', 'w').write(s)

