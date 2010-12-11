#! /usr/bin/python

# Copyright 2010, Google Inc.
# Author: Raph Levien (<firstname.lastname>@gmail.com)

#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# A script for subsetting a font, using FontForge.

import fontforge
import sys
import getopt
import os

def select_with_refs(font, unicode, newfont, pe = None):
    newfont.selection.select(('more', 'unicode'), unicode)
    if pe:
        print >> pe, "SelectMore(%d)" % unicode
    try:
        for ref in font[unicode].references:
            #print unicode, ref
            newfont.selection.select(('more',), ref[0])
            if pe:
                print >> pe, 'SelectMore("%s")' % ref[0]
    except:
        print 'Resolving references on u+%04x failed' % unicode

def subset_font_raw(font_in, font_out, unicodes, opts):
    if '--script' in opts:
        pe_fn = "/tmp/script.pe"
        pe = file(pe_fn, 'w')
    else:
        pe = None
    font = fontforge.open(font_in)
    print >> pe, 'Open("' + font_in + '")'
    for i in unicodes:
        select_with_refs(font, i, font, pe)
    if '--nmr' in opts:
        font.selection.select(('more',), 'nonmarkingreturn')
        if pe:
            print >> pe, 'SelectMore("%s")' % 'nonmarkingreturn'


    flags = ()

    if '--simplify' in opts:
        font.simplify()
        flags = ('omit-instructions',)

    if '--strip_names' in opts:
        font.sfnt_names = ()

    if '--new' in opts:
        font.copy()
        new = fontforge.font()
        new.encoding = font.encoding
        new.em = font.em
        new.layers['Fore'].is_quadratic = font.layers['Fore'].is_quadratic
        for i in unicodes:
            select_with_refs(font, i, new, pe)
        new.paste()
        # This is a hack - it should have been taken care of above.
        font.selection.select('space')
        font.copy()
        new.selection.select('space')
        new.paste()
        new.sfnt_names = font.sfnt_names
        font = new
    else:
        font.selection.invert()
        print >> pe, "SelectInvert()"
        font.cut()
        print >> pe, "Clear()"

    if pe:
        print >> pe, 'Generate("' + font_out + '")'
        pe.close()
        os.system("fontforge -script " + pe_fn)
    else:
        font.generate(font_out, flags = flags)
    font.close()

    if '--roundtrip' in opts:
        # FontForge apparently contains a bug where it incorrectly calculates
        # the advanceWidthMax in the hhea table, and a workaround is to open
        # and re-generate
        font2 = fontforge.open(font_out)
        font2.generate(font_out, flags = flags)

def subset_font(font_in, font_out, unicodes, opts):
    font_out_raw = font_out
    if not font_out_raw.endswith('.ttf'):
        font_out_raw += '.ttf';
    subset_font_raw(font_in, font_out_raw, unicodes, opts)
    if font_out != font_out_raw:
        os.rename(font_out_raw, font_out)

def getsubset(subset):
    subsets = subset.split('+')
    quotes = [0x2013, 0x2014, 0x2018, 0x2019, 0x201a, 0x201c, 0x201d, 0x201e,
              0x2022, 0x2039, 0x203a]
    latin = range(0x20, 0x7f) + range(0xa0, 0x100) + [0x20ac]
    result = quotes
    if 'latin' in subset:
        result += latin
    if 'latin-ext' in subset:
        # These ranges include Extended A, B, C, D, and Additional with the
        # exception of Vietnamese, which is a separate range
        result += (range(0x100, 0x250) +
                   range(0x1e00, 0x1ea0) +
                   range(0x1ef2, 0x1f00) +
                   range(0x20a0, 0x20d0) +
                   range(0x2c60, 0x2c80) +
                   range(0xa720, 0xa800))
    if 'vietnamese' in subset:
        result += range(0x1ea0, 0x1ef2) + [0x20ab]
    if 'greek' in subset:
        # Could probably be more aggressive here and exclude archaic characters,
        # but lack data
        result += range(0x370, 0x400)
    if 'greek-ext' in subset:
        result += range(0x370, 0x400) + range(0x1f00, 0x2000)
    if 'cyrillic' in subset:
        # Based on character frequency analysis
        result += range(0x400, 0x460) + [0x490, 0x491, 0x4b0, 0x4b1]
    if 'cyrillic-ext' in subset:
        result += (range(0x400, 0x530) +
                   [0x20b4] +
                   range(0x2de0, 0x2e00) +
                   range(0xa640, 0xa6a0))
    return result

def main(argv):
    optlist, args = getopt.gnu_getopt(argv, '', ['string=', 'strip_names',
                                                 'simplify', 'new', 'script',
                                                 'nmr', 'roundtrip', 'subset='])
    font_in, font_out = args
    opts = dict(optlist)
    if '--string' in opts:
        subset = map(ord, opts['--string'])
    else:
        subset = getsubset(opts.get('--subset', 'latin'))
    subset_font(font_in, font_out, subset, opts)

if __name__ == '__main__':
    main(sys.argv[1:])
