#!/usr/bin/env python3

'''
Reads allchips.txt (output from parseall.py) and creates ../../playtag/bsdl/data/partindex.txt

A part of playtag.
Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt
'''

import re
from collections import defaultdict

inp_fname = 'allchips.txt'
out_fname = '../../playtag/bsdl/data/partindex.txt'

def expand_x(s):
    def expander(s):
        if 'x' in s:
            a, b = s.rsplit('x', 1)
            for a in expander(a):
                s = (a, b)
                yield '0'.join(s)
                yield '1'.join(s)
        else:
            yield s
    return expander(s)

def union_x(s):
    s = list(s)
    result = s.pop()
    while s:
        a = s.pop()
        assert len(a) == len(result)
        result = ''.join(a == b and a or 'x' for a,b in zip(a,result))
    return result

def common_prefix(s):
    s = list(s)
    a = s.pop()
    for b in s:
        index = 0
        for index in range(min(len(a), len(b))):
            if a[index] != b[index]:
                break
        else:
            index += 1
        a = a[:index]
    return a

splitter = re.compile('([a-z_][a-z]*[0-9]*|[0-9]+|.)').split


packages = set('''
   _bare _quad _xxlj _xxln _xxjc csbga lqfp fbga tqfp _xxac _xxyc _xxvc bga _bga _mbga _pbga
   l044 t044 _j44 _pc44 _vq44 _xxt44 ael44 aet44 al44 bt44 at44 bl44 l044 t044 sq44 sl44 st44
   _tqfp48 _xxsn48 _xxt48 _xxtn48 _xxvc48 bt48 t048 qn48 zqn48 aeu49 _xxm56
   _xxsn64 _vq64 _xxmn64 _xxumn64 _j68 qn68 zm68 zqn68
   vf80 zuc81 zcs81 cs81
   _j84 _pc84 ael84  al84 l84 sl84 _96
   p100 _pq100 _q100 _tq100 _vq100 _xxm100 _xxp100 _xxt100 _xxtg100 _xxtn100 aef100 aet100 af100 at100 bt100 bf100 b100 q100
   m100 lvq100 t100 tq100 vq100 zm100 zvq100 sq100 xxfet100 st100
   qn108 _119 cs121 _xxt128 vq128 _128
   _cp132 _xxm132 _xxmg132 _xxumn132 qn132
   _cs144 _ht144 _tq144 _xxmn144 _xxp144 _xxt144 _xxtg144 _xxtn144 aet144 at144 bt144 b144 e144 et144 ef144 _144
   lfg144 fg144 t144 zm144 tq144 st144 xxfbd144
   _hq160 _pq160 _q160 _xxp160 _xxq160 sq160 _160 p160
   m164 _165 aeu169 _172 _ht176 _xxt176 vq176 _176 qn180 fet180 _192 cs196 cs201
   pq208 _hq208 _pq208 _xxb208 _xxp208 _xxq208 aeq208 eq208 aq208 fet208 bq208 cq208 fbd208 lpq208 q208 pq208 p208 sq208 xxfet208 r208 xxfbd208
   _209 _cb228
   _hq240 _pq240 aq240 bq240 cq240 eq240 ar240 q240 vq240 sq240 sr240 r240
   fg256 _bg256 _fg256 _ft256 _xftg256 _xxb256 _xxbg256 _xxf256 _xxft256 _xxftn256 aeb256 aef256 af256 bf256 b256 ef256 bb256 lfg256
   ffg256 sf256 zm256 gfg256 m256 fg256 _256
   _xxb272 bg272 _cs280 cs281 cs284 fcs288 gcs288 cs289 _pg299
   _hq304 r304 _fg320
   _xxf324 fg324 lfg324 ef324
   _xxbg332
   _bg352 cq352
   b356 ab356 cb356 eb356
   _xxf388
   _pg411
   _bg432
   _fg456 bg456
   fg474
   _xfpg484 _xx484 _xxf484 _xxfn484 af484 cf484 ef484 ff484 ffg484 fg484 gfg484 h484 lcg484 lfg484 llg484 sf484 wf484 vf484
   _xxfh516 _xxb544 _fg556 _pg559 _bg560 _cg560 _bg575 ag599 vg599
   eb600 ab600 cg624 b652 cb652 eb652
   _xx672 _xxf672 b672 cf672 df672 ef672 sf672
   fg676 _fg676 _xxf676 fg676
   _fg680 _xxfe680
   _cg717 b724 _bg728
   cf780 df780 ff780 h780 lf780 wf780
   _fg860
   _ff896 fg896 lcg896 lfg896 llg896
   _fg900 _xxf900
   _ef957
   _ffbga1020 df1020 ff1020 gf1020
   _cf1144 _ff1148
   _ef1152 _ff1152 _fpbga1152 _xxfc1152 ef1152 df1152 ff1152 fg1152 h1152 lf1152
   _fg1156 _xx1156 _xxfn1156
   _ff1517 ff1517 lf1517
   _ff1696
   _ef1704 _ff1704 _xxfc1704
   _civ_ffg1157  _civ_ffg1158 _civ_ffg1761 _civ_ffg1926 _civ_ffg1927 _civ_ffg1930 _civ_ffv1157
   _civ_ffv1158 _civ_ffv1927 _civ_ffva1156 _civ_ffva1517 _civ_ffva1760 _civ_ffva2104 _civ_ffva676
   _civ_ffvb1760 _civ_ffvb2104 _civ_ffvb676 _civ_ffvc1517 _civ_ffvc2104 _civ_ffvd1517 _civ_ffvd900
   _civ_ffve1517 _civ_ffve1760 _civ_ffvj1760 _civ_fhga2104 _civ_fhgb2104 _civ_fhgc2104 _civ_figd2104
   _civ_flga2104 _civ_flga2577 _civ_flga2892 _civ_flgb2104 _civ_flgb2377 _civ_flgc2104 _civ_flgf1924
   _civ_flva1517 _civ_flva2104 _civ_flvb1760 _civ_flvb2104 _civ_flvc2104 _civ_flvd1517 _civ_flvd1924
   _civ_flvf1924 _civ_fsga2577 _civ_fsgd2104 _civ_fsva3824 _civ_fsvb3824 _civ_fsvh1924 _civ_fsvh2104
   _civ_fsvh2892 _civ_fsvj1760 _civ_fsvk2892 _civ_sfvb784 _civ_vsva1365 _cl400 _cl484 _clg225 _clg400
   _clg484 _clg485 _cna1509 _cpg236 _cpg238 _cpga196 _cs324 _cs325 _csg324 _csg325 _csga225 _csga324
   _fbg484 _fbg676 _fbg900 _fbv484 _fbv676 _fbv900 _fbva676 _fbva900 _fbvb900 _ff900 _ffg1156 _ffg1157
   _ffg1158 _ffg1761 _ffg1926 _ffg1927 _ffg1928 _ffg1930 _ffg676 _ffg900 _ffg901 _ffv1156 _ffv1157
   _ffv1158 _ffv1761 _ffv1927 _ffv676 _ffv900 _ffv901 _ffva1156 _ffva1517 _ffva1760 _ffva2104 _ffva676
   _ffvb1156 _ffvb1517 _ffvb1760 _ffvb2104 _ffvb676 _ffvc1156 _ffvc1517 _ffvc1760 _ffvc2104 _ffvc900
   _ffvd1156 _ffvd1517 _ffvd1760 _ffvd900 _ffve1156 _ffve1517 _ffve1760 _ffve1924 _ffve900 _ffvf1517
   _ffvf1760 _ffvg1517 _ffvh1760 _ffvj1760 _fg484 _fgg484 _fgg676 _fgga484 _fgga676 _fhg1761
   _fhga2104 _fhgb2104 _fhgc2104 _figd2104 _flg1155 _flg1925 _flg1926 _flg1928 _flg1930 _flg1931
   _flg1932 _flga2104 _flga2577 _flga2892 _flgb2104 _flgb2377 _flgc2104 _flgf1924 _flva1517
   _flva2104 _flvb1760 _flvb2104 _flvc2104 _flvd1517 _flvd1924 _flvf1924 _fsga2577 _fsgd2104
   _fsva3824 _fsvb3824 _fsve1156 _fsvf1760 _fsvg1517 _fsvh1760 _fsvh1924 _fsvh2104 _fsvh2892
   _fsvj1760 _fsvk2892 _ftg256 _ftgb196 _hcg1155 _hcg1931 _hcg1932 _lsvc4072 _nbvb1024
   _rb484 _rb676 _rf1156 _rf1157 _rf1158 _rf1761 _rf1930 _rf676 _rf900 _rs484 _sbg484 _sbg485
   _sbv484 _sbv485 _sbva484 _sfva625 _sfva784 _sfvb784 _sfvc784 _ubva530 _vfvb1024 _vfvc1760
   _viva1596 _vsva1365 _vsva2197 _vsva2785 _vsva3340 _vsva3697 _vsvd1760
'''.split())

def prune(tree, prefix):
    if None in tree:
        return ()
    result = dict((x, prune(y, prefix+x)) for (x,y) in tree.items())
    if not max(len(x) for x in result.values()):
        result = set(result)
        if len(prefix) > 3 and (result & packages):
            result = ()
    return result

def untree(tree):
    if isinstance(tree, dict):
        for x,y in tree.items():
            for y in untree(y):
                yield x+y
    elif tree:
        for x in tree:
            yield x
    else:
        yield ''

def minprefixes(names, required=4):
    counts = [len(x) for x in names]
    index = len(names) -2
    for index in range(len(names) - 2, -1, -1):
        common = common_prefix(names[index:index+2])
        if len(common) >= required:
            names[index:index+2] = [common]
            counts[index:index+2] = [min(counts[index:index+2])]
    return [x + (y - len(x)) * 'x' for (x,y) in zip(names, counts)]

def combine_name(namelist, splitter=splitter):
    nametree = {}
    if 0:
        print(common_prefix(namelist), namelist)
        print('     ', [[x for x in splitter(x) if x] for x in namelist])
        print()
    if 1:
        for name in namelist:
            d = nametree
            for piece in (x for x in splitter(name) if x):
                d = d.setdefault(piece, {})
            d[None] = None
        nametree = prune(nametree, '')
        names = sorted((untree(nametree)))
        if len(names) == 1:
            return names[0]
        return '/'.join(sorted(minprefixes(names)))

class SynthesizedPart(object):
    pass

def checkpart(items, item_names='ilength icapture idcode'.split()):
    nm = sorted(set(x.name.lower() for x in items))
    il = set(x.instruction_length for x in items)
    ic = set(x.instruction_capture for x in items)
    id = set(x.idcode_register for x in items)
    if len(id) > 1:
        new_id = union_x(id)
        if new_id in id or new_id.count('x') <= 8:
            id = set([new_id])
    if len(ic) > 1:
        new_ic = union_x(ic)
        if new_ic in ic:
            ic = set([new_ic])
    result = []
    for name, value in zip(item_names, (il, ic, id)):
        if len(value) > 1:
            result.append((name, value))
    if result:
        print('Removing collisions', nm)
        for stuff in result:
            print('    %s = %s' % stuff)
        return None
    result = SynthesizedPart()
    result.instruction_length, = il
    result.instruction_capture, = ic
    result.idcode_register, =  id
    if len(nm) > 1:
        nm[0] = combine_name(nm)
    result.name = nm[0]
    return result

def check_collisions(source):
    bigdict = defaultdict(list)
    for part in source:
        for idcode in expand_x(part.idcode_register):
            bigdict[idcode].append(part)
    collisions = defaultdict(set)
    for stuff in bigdict.values():
        if len(stuff) > 1:
            for part in stuff:
                collisions[part].update(stuff)
    parts = sorted(source, key=lambda x:x.name.lower())
    processed = set()
    result = []
    for part in parts:
        if part not in collisions:
            if part not in processed:
                result.append(part)
            continue
        checkset = set()
        unchecked = set([part])
        while unchecked:
            part = unchecked.pop()
            checkset.add(part)
            unchecked.update(collisions.pop(part) - checkset)
        processed.update(checkset)
        part = checkpart(checkset)
        if part is not None:
            result.append(part)
    return result

def strip_silly(source):
    total = 0
    silly = 0
    withx = []
    for part in parts:
        idcode = part.idcode_register.lower()
        ok = idcode[0] == idcode[-1] == '"' and len(idcode) == 34
        idcode = idcode[1:-1].strip()
        ok = ok and idcode[-12:].count('x') == 0
        ok = ok and idcode[-1] == '1' and len(set(idcode[-8:-1])) == 2
        ok = ok and idcode[4:-12].count('x') < 16
        ilength = part.instruction_length
        ilength = ilength.isdigit() and int(ilength)
        ok = ok and ilength
        icapture = part.instruction_capture.lower()
        ok = ok and icapture[0] == icapture[-1] == '"'
        icapture = icapture[1:-1].strip()
        ok = ok and len(icapture) == ilength
        ok = ok and icapture[-2:] == '01'
        if ok:
            part.idcode_register = idcode
            part.instruction_capture = icapture
            part.instruction_length = ilength
        else:
            print("Ignoring silly part", idcode, part.name, part.instruction_length, part.instruction_capture, part.bsdl_file_name)
            silly += 1
            continue
        numx = idcode.count('x')
        withx.append((numx, part))
        total += 1 << numx
    print()
    print("Ignored %s silly parts" % silly)
    withx.sort()
    print("Largest number of x's in a non-silly ID code --", withx[-1][0])
    print("%s part records covering %s possible ID Codes" % (len(withx), total))
    assert total < 200000, total   # Would take too long
    return [x[1] for x in withx]

class Part(str):
    def __init__(self, name):
        self.name = name

def readfile(fname=inp_fname):

    parts = []

    for line in open(fname, 'rt').read().splitlines():
        if line.startswith(' '):
            name, value = line.split('=', 1)
            setattr(part, name.strip(), value.strip())
        else:
            part = Part(line.strip())
            parts.append(part)
    return parts

def readdest(fname=out_fname):

    parts = []

    for line in open(fname, 'rt').read().splitlines():
        line = line.split()
        if not line:
            continue
        assert len(line) == 3, line
        p = Part(line[2])
        p.idcode_register = '"%s"' % line[0]
        p.instruction_length = str(len(line[1]))
        p.instruction_capture = '"%s"' % line[1]
        p.bsdl_file_name = 'preexisting'
        parts.append(p)
    return parts

def dump(parts, fname=out_fname):
    def sortkey(x):
        x = x.idcode_register.replace('x', '/')
        assert len(x) == 32
        return x[-12:] + x[4:-12] + x[:4]

    parts.sort(key=sortkey)
    f = open(fname, 'wt')
    for part in parts:
        assert part.instruction_length == len(part.instruction_capture)
        print('%s  %-20s %s' % (part.idcode_register, part.instruction_capture, part.name.lower()), file=f)
    f.close()

if __name__ == '__main__':
    parts = readfile() + readdest()
    parts = strip_silly(parts)
    parts = check_collisions(parts)
    print('%s records after removing redundancies' % len(parts))
    dump(parts)
