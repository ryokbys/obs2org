#!/usr/bin/env python
"""
Convert markdown file in Obsidian to org file.
Output-file name is automatically determined by replacing the extension
of input file from .md to .org and save to the working directory.

Usage:
  obs2org.py [options] INFILE

Options:
  -h, --help  Show this message and exit.
  --daily-path DAILY_PATH
              Relative path from base obsidian directory to daily-note directory. [default: ./]
  --asset-path ASSET_PATH
              Relative path from base obsidian directory to asset directory. [default: ./]
"""
from __future__ import print_function

import os,sys
from docopt import docopt
import re
import copy
from os.path import abspath, basename, dirname

__author__ = "RYO KOBAYASHI"
__version__ = ""

def convert_links(line0,daily_path='.',asset_path='.',is_daily=False):
    """
    Special function to convert links from obsidian type to org type.
    """
    line = copy.copy(line0)

    if not re.search(r'(\[.+\])',line):  # if no match, do nothing and skip
        return line

    #...Store literals
    #...But since it should be very rare that link-like text is in literals,
    #...Let's skip to consider this...
    literals = []
    for s in re.finditer(r'`[^`]+`',line):
        literals.append(s)

    if is_daily:
        prefix = '../'
    else:
        prefix = ''
    
    #...Wiki-like image links
    line = re.sub(r'!\[\[([^(\[|\]|\]\[)]+\.(jpg|jpeg|png|pdf|docx|pptx|cif))\]\]',
                  r'![[file:{0:s}{1:s}\1]]'.format(prefix,asset_path+'/'),
                  line)
    #...Wiki-like links to daily notes
    line = re.sub(r'\[\[(\d{4}-\d\d-\d\d)\]\]',
                  r'[[file:{0:s}{1:s}\1.org]]'.format(prefix,daily_path+'/'),
                  line)
    #...Wiki-like md-file links
    line = re.sub(r'\[\[(?!file:)([^\]\[]+)\]\]',
                  r'[[file:{0:s}\1.org][\1]]'.format(prefix),
                  line)

    #...Image link with `https?:`
    line = re.sub(r'!\[([^(\[|\]|\]\[)]+)\]\((https?:[^\)]+)\)',
                  r'![[\2][\1]]',
                  line)
    #...Normal link with `https?:`
    line = re.sub(r'\[([^(\[|\]|\]\[)]+)\]\((https?:[^\)]+)\)',
                  r'[[\2][\1]]',
                  line)

    #...Image link to a local file (can be non-image file like pdf)
    line = re.sub(r'!\[([^(\[|\]|\]\[)])\]\(([^\)]+)\)',
                  r'![[file:\2][\1]]',
                  line)
    #...Normal link to a local file
    line = re.sub(r'\[([^(\[|\]|\]\[)])\]\(([^\)]+)\)',
                  r'[[file:\2][\1]]',
                  line)

    return line


def convert_footnotes(line0):
    line = copy.copy(line0)
    line = re.sub(r'\[\^([^\]]+)\]:?',
                  r'[fn:\1]',line)
    return line
    

def md2org(infile,outfile,daily_path='daily',asset_path='assets',is_daily=False):
    """
    Convert markdown text in my obsidian vault to org format text.

    - If tags are set around the header of the file such as `tags: #foo #bar`,
      they are convert to `#+ROAM_TAGS: foo bar`
    - If title is set around the header of the file as `# Title`,
      use the title as `#+TITLE: Title`.
      Otherwise, use the filename as title.
    - If the title is obtained from `# Title`, `## Section` is converted to `* Section`
      by reducing the number of bullets, otherwise just convert `##` to `**` without
      changing the number of #s.
    - If words or text are sandwiched with "`" or "```",
      they are treated as verbose text and not to consider as code block.
    - Inline code, `code`, is converted to ~code~.
      Code block with "```" is converted to #+begin_src ... #+end_src.
      If any language is specified to ```, that is added #+begin_src as well.
    - Both inline or line math formula are not converted as they can be also used in org, too.
    - Link with the style [TEXT](LINK) or ![TEXT](LINK) is converted to
      [[LINK][TEXT]] if the LINK is a file, add `file:` at the beginning of LINK.
    - Link with the style [[]] or ![[]] are converted to [[file:][]]
      regardless they are link to markdown or other format.
      But the link [[YYYY-MM-DD]] is converted to [[file:daily_path/YYYY-MM-DD][YYYY-MM-DD]],
      and the link ![[LINK]] to [[file:image/LINK][LINK]] regardless the LINK is an image file or not.
    - Above rules for link can be different for daily notes as they are in daily_path/ directory.
      The link, [[LINK]],  should become like [[file:../LINK][LINK]].
    - List without preceding blank line is also considered as list block.
    - Horizontal bar --- is converted as ----- (more than 5 hyphens).
    - `**BOLD**` to `*BOLD*`
    - `*ITALIC*` to `/ITALIC/`
    - `~STRIKE~` to `+STRIKE+`
    - ``CODE`` to `~CODE~`
    """

    with open(infile,'r') as f:
        intxt = f.readlines()
    outtxt = []
    
    #...Check header up to 10 lines
    tags = []
    if is_daily:
        title = basename(infile).split('.')[0]
        title_exsits = False
    else:
        title = ''
        title_exists = False
        for il,line in enumerate(intxt[0:10]):
            if line[0:2] == '# ':  # Title exists
                title = line.replace('# ','').strip()
                title_exists = True
            else:
                title = os.path.basename(infile).replace('.md','')
            if 'tags:' in line:  # Tags exist
                line1 = line.replace('tags: ','')
                entries = line1.split()
                tags = [ e.replace('#','') for e in entries ]
    # print(title)
    # print(tags)

    outtxt.append('#+TITLE: {0:s}\n'.format(title))
    if len(tags) > 0:
        roam_tags = '#+ROAM_TAGS:'
        for t in tags:
            roam_tags += ' {0:s}'.format(t)
        roam_tags += '\n'
        outtxt.append(roam_tags)
        
    outtxt.append('\n')

    re_sec = re.compile('^#+\s')
    re_code = re.compile('`[^`]+`')

    is_codeblock = False
    for il,line in enumerate(intxt):
        if is_daily and il < 7:
            continue
        if line[0:2] == '# ':
            continue
        if il < 10 and 'tags: ' in line:
            continue
        if "```" in line:
            if not is_codeblock:  # No need of processing text
                is_codeblock = True
                lineout = line.replace('```','#+begin_src ')
            else:
                is_codeblock = False
                lineout = line.replace('```','#+end_src')
        else:
            if is_codeblock:
                lineout = line
            else:
                lineout = line
                #...Sections
                if re.match(r'#+\s',lineout):  # sections
                    lineout = re.sub(r'#',r'*',lineout)
                #...Links
                lineout = convert_links(lineout,daily_path,asset_path,is_daily)
                #...Bold
                lineout = re.sub(r'\s*\*\*([^\*]+)\*\*\s*[^\n]',r' *\1* ',lineout)
                #...Italic
                lineout = re.sub(r'\s*\*([^\*]+)\*\s*[^\n]',r' /\1/ ',lineout)
                #...Strike
                lineout = re.sub(r'\s*~([^~]+)~\s*[^\n]',r' +\1+ ',lineout)
                #...Code
                lineout = re.sub(r'\s*`([^`]+)`\s*[^\n]',r' ~\1~ ',lineout)
                #...Holizontal rule
                lineout = re.sub(r'-{3,}',r'-----',lineout)
                #...Footnotes
                lineout = convert_footnotes(lineout)

        outtxt.append(lineout)
        
    
    assert(outtxt is not [])
    with open(outfile,'w') as f:
        for l in outtxt:
            f.write(l)
        f.write('\n')
        
    return None
    

if __name__ == "__main__":

    args = docopt(__doc__)
    infile = args['INFILE']
    basedir = basename(dirname(abspath(infile)))
    outfile = dirname(abspath(infile))+'/'+basename(infile).replace('.md','.org')
    #outfile = infile.split('/')[-1].replace('.md','.org')
    daily_path = args['--daily-path']
    asset_path = args['--asset-path']

    if basedir in daily_path:
        is_daily = True
    else:
        is_daily = False

    md2org(infile,outfile,
           daily_path=daily_path,
           asset_path=asset_path,
           is_daily=is_daily)

    print(' Wrote {0:s}'.format(outfile))
