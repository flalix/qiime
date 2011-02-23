#!/usr/bin/env python
# File created on 27 Oct 2009.
from __future__ import division

__author__ = "Greg Caporaso"
__copyright__ = "Copyright 2010, The QIIME Project"
__credits__ = ["Greg Caporaso", "Kyle Bittinger"]
__license__ = "GPL"
__version__ = "1.2.1-dev"
__maintainer__ = "Greg Caporaso"
__email__ = "gregcaporaso@gmail.com"
__status__ = "Development"

from optparse import make_option
from os import makedirs
from qiime.util import load_qiime_config, parse_command_line_parameters
from qiime.parse import parse_qiime_parameters
from qiime.workflow import run_qiime_data_preparation, print_commands,\
    call_commands_serially, print_to_stdout, no_status_updates

qiime_config = load_qiime_config()

script_info={}
script_info['brief_description'] = """A workflow script for picking OTUs through building OTU tables"""
script_info['script_description'] = """This script takes a sequence file and performs all processing steps through building the OTU table.

REQUIRED: You must add values for the following parameters in a custom parameters file:
 align_seqs:template_fp
 filter_alignment:lane_mask_fp 
 
These are the values that you would typically pass as --template_fp to align_seqs.py and lane_mask_fp to filter_alignment.py, respectively.


"""

script_info['script_usage'] = []

script_info['script_usage'].append(("""Simple example""","""The following command will start an analysis on inseq1.fasta (-i), which is a post-split_libraries fasta file. The sequence identifiers in this file should be of the form <sample_id>_<unique_seq_id>. The following steps, corresponding to the preliminary data preparation, are applied.

1. Pick OTUs with uclust at similarity of 0.97;

2. Pick a representative set with the most_abundant method;

3. Align the representative set with PyNAST (REQUIRED: SPECIFY TEMPLATE ALIGNMENT with align_seqs:template_fp in the parameters file);

4. Assign taxonomy with RDP classifier;

5. Filter the alignment prior to tree building - remove positions which are all gaps, and specified as 0 in the lanemask (REQUIRED: SPECIFY LANEMASK with filter_alignment:lane_mask_fp in the parameters file);

6. Build a phylogenetic tree with FastTree;

7. Build an OTU table.

All output files will be written to the directory specified by -o, and 
subdirectories as appropriate.
""","""pick_otus_through_otu_table.py -i inseqs1.fasta -o wf1/ -p custom_parameters.txt"""))

script_info['script_usage'].append(("""Simple example with denoising""","""This command will do the same steps as the previous example and additionally denoise the data set prior to OTU picking. Only flowgrams in the input sff.txt file that have a matching identifier in inseqs1.fasta are considered here, the rest is discarded.

1. Denoise flowgrams in inseqs1.sff.txt;

2. Pick OTUs with uclust at similarity of 0.97;

3. Pick a representative set with the most_abundant method;

4. Align the representative set with PyNAST (REQUIRED: SPECIFY TEMPLATE ALIGNMENT with align_seqs:template_fp in the parameters file);

5. Assign taxonomy with RDP classifier;

6. Filter the alignment prior to tree building - remove positions which are all gaps, and specified as 0 in the lanemask (REQUIRED: SPECIFY LANEMASK with filter_alignment:lane_mask_fp in the parameters file);

7. Build a phylogenetic tree with FastTree;

8. Build an OTU table.

All output files will be written to the directory specified by -o, and 
subdirectories as appropriate.
""","""pick_otus_through_otu_table.py -s inseqs1.sff.txt -m metadata_mapping.txt -i inseqs1.fasta -o wf2/ -p custom_parameters.txt"""))

script_info['output_description'] ="""This script will produce a set of cluster centroids (as a FASTA file) and a cluster mapping file (from denoise.py if sff.txt and mapping file were provided), an OTU mapping file (pick_otus.py), a representative set of sequences (FASTA file from pick_rep_set.py), a sequence alignment file (FASTA file from align_seqs.py), taxonomy assignment file (from assign_taxonomy.py), a filtered sequence alignment (from filter_alignment.py), a phylogenetic tree (Newick file from make_phylogeny.py) and an OTU table (from make_otu_table.py)."""

script_info['required_options'] = [
    make_option('-i','--input_fp',
        help='the input fasta file [REQUIRED]'),
    make_option('-o','--output_dir',
        help='the output directory [REQUIRED]'),
    make_option('-p','--parameter_fp',
        help='path to the parameter file [REQUIRED]'),
    ]

script_info['optional_options'] = [\
 make_option('-f','--force',action='store_true',\
        dest='force',help='Force overwrite of existing output directory'+\
        ' (note: existing files in output_dir will not be removed)'+\
        ' [default: %default]'),\
 make_option('-w','--print_only',action='store_true',\
        dest='print_only',help='Print the commands but don\'t call them -- '+\
        'useful for debugging [default: %default]',default=False),\
 make_option('-a','--parallel',action='store_true',\
        dest='parallel',default=False,\
        help='Run in parallel where available [default: %default]'),\
 make_option('-m','--mapping_fp',
        help='the mapping filepath [REQUIRED for denoising]'),
 make_option('-s','--sff_fp',
        help='the sff file [REQUIRED for denoising]'),
]
script_info['version'] = __version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)

    verbose = opts.verbose
    
    input_fp = opts.input_fp
    output_dir = opts.output_dir
    verbose = opts.verbose
    print_only = opts.print_only
    
    parallel = opts.parallel
    # No longer checking that jobs_to_start > 2, but
    # commenting as we may change our minds about this.
    #if parallel: raise_error_on_parallel_unavailable()
    
    try:
        parameter_f = open(opts.parameter_fp)
    except IOError:
        raise IOError,\
         "Can't open parameters file (%s). Does it exist? Do you have read access?"\
         % opts.parameter_fp
         
    if opts.sff_fp or opts.mapping_fp:
        assert opts.sff_fp and opts.mapping_fp,\
         "The sff and mapping fp are only required when denoising, "+\
         "and both must be provided in that case."
    
    try:
        makedirs(output_dir)
    except OSError:
        if opts.force:
            pass
        else:
            # Since the analysis can take quite a while, I put this check
            # in to help users avoid overwriting previous output.
            print "Output directory already exists. Please choose "+\
             "a different directory, or force overwrite with -f."
            exit(1)
        
    if print_only:
        command_handler = print_commands
    else:
        command_handler = call_commands_serially
    
    if verbose:
        status_update_callback = print_to_stdout
    else:
        status_update_callback = no_status_updates
    
    run_qiime_data_preparation(
     input_fp, 
     output_dir,
     command_handler=command_handler,
     params=parse_qiime_parameters(parameter_f),
     qiime_config=qiime_config,
     sff_input_fp=opts.sff_fp, 
     mapping_fp=opts.mapping_fp,
     parallel=parallel,\
     status_update_callback=status_update_callback)

if __name__ == "__main__":
    main()    
