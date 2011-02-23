#!/usr/bin/env python
# File created on 19 Jan 2011
from __future__ import division

__author__ = "Jesse Stombaugh"
__copyright__ = "Copyright 2011, The QIIME project"
__credits__ = ["Jesse Stombaugh","Julia Goodrich", "Justin Kuczynski"]
__license__ = "GPL"
__version__ = "1.2.1-dev"
__maintainer__ = "Jesse Stombaugh"
__email__ = "jesse.stombaugh@colorado.edu"
__status__ = "Development"
"""
This script generates taxonomy charts
"""

from qiime.util import parse_command_line_parameters, get_qiime_project_dir
from optparse import make_option
from qiime.plot_taxa_summary import make_all_charts
from cogent.util.misc import get_random_directory_name
from qiime.colors import taxonomy_color_prefs_and_map_data_from_options
import re
import matplotlib
import os
import shutil

plot_filetype_choices = ['pdf','svg','png']

script_info={}
script_info['brief_description']="""Make taxaonomy summary charts based on taxonomy assignment"""
script_info['script_description']="""This script automates the construction of pie, bar and area charts showing the breakdown of taxonomy by given levels. The script creates an html file for each chart type for easy visualization. It uses the taxonomy or category counts from summarize_taxa.py for combined samples by level (-i) and user specified labels for each file passed in (-l). Output will be written to the user specified folder (-o) the, where the default is the current working directory. The user can also specify the number of categories displayed for within a single pie chart, where the rest are grouped together as the 'other category' using the (-n) option, default is 20.
"""
script_info['script_usage']=[]
script_info['script_usage'].append(("""Examples:""","""If you wish to run the code using default parameters, you must supply a counts file (Class.txt) along with the taxon level label (Class) and the type(s) of chart, by using the following command:""","""plot_taxa_summary.py -i Class.txt -l Class -c pie,bar,area"""))
script_info['script_usage'].append(("""""","""If you want to make charts for multiple levels at a time (phylum.txt,class.txt,genus.txt) use the following command:""","""plot_taxa_summary.py -i phylum.txt,class.txt,genus.txt -l phylum,class,genus -c pie,bar,area"""))
script_info['script_usage'].append(("""""","""If you want specify an output directory (e.g. "output_charts/", regardless of whether the directory exists, use the following command:""","""plot_taxa_summary.py -i Class.txt -l Class -c pie,bar,area -o output_charts/"""))
script_info['script_usage'].append(("""""","""Additionally, if you would like to display on a set number of taxa ("-n 10") in the pie charts, you can use the following command:""","""plot_taxa_summary.py -i Class.txt -l Class -c pie -o pie_charts/ -n 10"""))
script_info['script_usage'].append(("""""","""If you would like to display generate pie charts for samples samples: 'sample1' and 'sample2' that are in the counts file header, you can use the following command:""","""plot_taxa_summary.py -i Class.txt -l Class -o pie_charts/ -b sample1,sample2"""))
script_info['output_description']="""The script generates an output folder, which contains several files. For each pie chart there is a png and a pdf file. The best way to view all of the pie charts is by opening up the file taxonomy_summary_pie_chart.html."""

script_info['required_options']=[\
make_option('-i', '--input_files', dest='counts_fname',\
    action='store',type='string',\
    help='list of files with sample counts by taxonomy [REQUIRED]'),
make_option('-l', '--labels', dest='labels',action='store',type='string',
    help='list of labels (i.e. Phylum, Class) [REQUIRED]')
]

script_info['optional_options']=[\
make_option('-n', '--num', dest='num_categories', \
    help='Maximum number of individual categories in each pie chart. \
All additional categories are grouped into an "other" category. \
NOTE: this is only used for the pie charts. \
[default: %default]', default='20'),
make_option('-o', '--dir-prefix', dest='dir_path',\
    help='output folder'),
make_option('-b', '--colorby', dest='colorby',\
    help='This is the samples to make charts for in the counts files from \
summarize_taxa.py. The sample name must match the name of a sample id \
in the header of the counts file exactly and multiple categories can be \
list by comma separating them without spaces. \
 [default: %default]',default=None),
 make_option('-p', '--prefs_path',help='This is the user-generated preferences \
file. NOTE: This is a file with a dictionary containing preferences for the \
analysis. The label taxonomy_coloring is used for the coloring, see example \
prefs file preferences_file. [default: %default]'),
 make_option('-k', '--background_color',help='This is the background color to \
use in the plots. [default: %default]'),
 make_option('-d', '--dpi',help='This is the dpi to \
use in the plots. [default: %default]',default='80'),
 make_option('-x', '--x_width',help='This is the width to \
use in the plots. [default: %default]',default='12'),
 make_option('-y', '--y_height',help='This is the height to \
use in the plots. [default: %default]',default='6'),
make_option('-w', '--bar_width', dest='bar_width', \
    help='This the width of the bars in the bar graph and should be a number between 0 and 1. NOTE: this is only used for bar charts. [default: %default]', default='0.75'),
 make_option('-t', '--type_of_file',type='choice',help='This is the filename suffix to use for each high-res plot. (i.e. '+','.join(plot_filetype_choices)+') [default: %default]', choices=plot_filetype_choices,default='pdf'),
 make_option('-c', '--chart_type', dest='chart_type',\
     action='store',type='string',\
     help='type of chart to plot (i.e. pie, bar or area). The user has the ability to plot multiple types, by using a comma-separated list (e.g. area,pie)\
  [default: %default]',default='area,bar'),
 make_option('-r', '--resize_nth_label', dest='resize_nth_label',\
    action='store',type='string',\
    help='this is for large area and bar charts where the font on the x-axis is small. This allows you to set every nth label to be larger on the x-axis.This requires an integer value greater than 0.\
[default: %default]',default='0')
]

script_info['version']=__version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)
    
    #Check the version of Matplotlib
    matplotlib_version = re.split("[^\d]", matplotlib.__version__)
    matplotlib_version_info = tuple([int(i) for i in matplotlib_version if \
                            i.isdigit()])
    if matplotlib_version_info != (0,98,5,3) and \
        matplotlib_version_info != (0,98,5,2):
        print "This code was only tested with Matplotlib-0.98.5.2 and \
              Matplotlib-0.98.5.3"

    #get QIIME directory
    qiime_dir=get_qiime_project_dir()

    if not opts.counts_fname:
        option_parser.error("A list of input files must be specified")
    if not opts.labels:
        option_parser.error(\
            "A list of label names cooresponding to files must be specified")

    #get color preferences
    color_prefs, color_data, background_color, label_color= \
                   taxonomy_color_prefs_and_map_data_from_options(opts)
    
    colorby = opts.colorby
    if colorby==None:
        colorby=[]
        for c in color_data['counts'].values():
            colorby.extend(c[0])
    else:
        colorby=colorby.strip().strip("'").split(',')
    
    counts_fname = opts.counts_fname
    
    #Define labels to use
    labels = opts.labels
    data = [(label,f.strip()) \
        for f,label in zip(counts_fname.split(","),labels.split(","))]
    filepath=data[0][1]
    
    filename=filepath.strip().rpartition('/')[0]
    num_categories = int(opts.num_categories)
    if num_categories<=0:
        raise ValueError, 'The number of categories has to be greater than 0!'

    #create directory path
    if opts.dir_path:
        if os.path.exists(opts.dir_path):
            dir_path=opts.dir_path
        else:
            try:
                os.mkdir(opts.dir_path)
                dir_path=opts.dir_path
            except OSError:
                pass
    else:
        dir_path='./'
        
    if dir_path == './':
        dir_path = os.getcwd()

    #make javascript output directory
    javascript_path = os.path.join(dir_path,'js')
    try:
        os.mkdir(javascript_path)
    except OSError: #raised if dir exists
        pass
        
    #make raw_data output directory
    raw_data_path = os.path.join(dir_path,'raw_data')
    try:
        os.mkdir(raw_data_path)
    except OSError: #raised if dir exists
        pass
        
    # move javascript file to javascript output directory
    shutil.copyfile(os.path.join(qiime_dir,'qiime','support_files',\
                    'js/overlib.js'),\
                    os.path.join(javascript_path,'overlib.js'))

    #make css output directory
    css_path = os.path.join(dir_path,'css')
    try:
        os.mkdir(css_path)
    except OSError: #raised if dir exists
        pass
        
    # move css file to css output directory
    shutil.copyfile(os.path.join(qiime_dir,'qiime','support_files',\
                    'css/qiime_style.css'),\
                    os.path.join(css_path,'qiime_style.css'))

    # verify all parameters are valid
    plot_width=float(opts.x_width)
    if plot_width<=0:
        raise ValueError, 'The width of the plot has to be greater than 0!'
    
    plot_height=float(opts.y_height)
    if plot_height<=0:
        raise ValueError, 'The height of the plot has to be greater than 0!'
    
    bar_width=float(opts.bar_width)
    if bar_width<=0 or bar_width>1:
        raise ValueError, 'The bar width of the plot has to be between 0 and 1!'

    dpi=float(opts.dpi)    
    if dpi<=0:
        raise ValueError, 'The dpi of the plot has to be greater than 0!'
    
    resize_nth_label=int(opts.resize_nth_label)
    if resize_nth_label<0:
        raise ValueError, 'The resize_nth_label of the plot has to be greater than 0!'
    
    generate_image_type=opts.type_of_file
    plots_to_make=opts.chart_type.split(',')
    chart_types=['area','pie','bar']
    for i in plots_to_make:
        chart_type=i.lower().strip()
        if chart_type not in chart_types:
            raise ValueError, 'Please type in one of the appropriate chart types (i.e. %s)!' % ','.join(chart_types) 
            
        #make pie chart output path
        charts_path = os.path.join(dir_path,'charts')
        try:
            os.mkdir(charts_path)
        except OSError: #raised if dir exists
            pass
        
        make_all_charts(data,dir_path,filename,num_categories, \
        colorby,args,color_data, color_prefs,background_color,label_color,\
        chart_type,generate_image_type,plot_width,plot_height,bar_width,dpi,\
        resize_nth_label)
        
    
if __name__ == "__main__":
    main()
