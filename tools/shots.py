#!/usr/bin/env python3
"""shots.py - screenshots of Stronkie's Olympics for the readme and itch.io: python3 tools/shots.py <which>"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import harness
OUT = os.path.join(os.path.dirname(__file__), '..', 'screenshots')
w = sys.argv[1]
def s16(v): return v - 65536 if v & 0x8000 else v
if w == 'menu':
    g = harness.Game(exe='build/full/SOlymp.game', mapf='build/full/SOlymp.map', datadir='build/full', out=OUT)
    g.hook(['k_input', 'medals'])
    g.run(470); g.shot('03_opening')
    g.fire(4); g.idle(); g.run(60); g.shot('01_title')
    g.fire(6); g.idle()
    for k in (0x41,) * 8: g.key(k, 3)
    for k in (0x37, 0x20, 0x13, 0x15): g.key(k, 4)
    g.joy('down'); g.joy('down'); g.joy('right'); g.run(20); g.shot('02_create')
elif w == 'soccer':
    g = harness.event_game(1, out=OUT); g.idle(); g.run(90)
    g.run(9); g.fire(2); g.run(10); g.shot('04_soccer_aim')
    g.run(6); g.fire(2); g.run(16); g.shot('05_soccer_shot')
    g.run(100); g.am.joy['right'] = 1; g.run(40); g.am.joy['right'] = 0; g.shot('06_soccer_keeper')
elif w == 'basket':
    g = harness.event_game(2, out=OUT); g.idle(); g.run(60)
    g.am.joy['fire'] = 1; g.run(30); g.am.joy['fire'] = 0; g.run(16); g.shot('07_basketball')
elif w == 'volley':
    g = harness.event_game(3, out=OUT); g.idle(); g.run(30)
    E = harness.ev_addr(g, 'build/Volley.map'); g.fire(4)
    for i in range(400):
        bx = s16(g.am.rw(E('bx'))) >> 4; px = s16(g.am.rw(E('px'))) + 16
        g.am.joy['left'] = 1 if bx < px - 4 else 0; g.am.joy['right'] = 1 if bx > px + 4 else 0
        g.run(1)
        by = s16(g.am.rw(E('by'))) >> 4
        if i > 150 and 90 < by < 150 and g.am.rb(E('ball_on')): break
    g.shot('08_volleyball')
elif w == 'bowling':
    g = harness.event_game(4, out=OUT); g.idle(); g.run(30)
    g.am.joy['right'] = 1; g.run(4); g.am.joy['right'] = 0
    g.run(4); g.fire(3); g.run(12); g.fire(3); g.run(14); g.fire(3); g.run(66); g.shot('09_bowling')
elif w == 'surf':
    g = harness.event_game(5, out=OUT); g.idle(); g.run(40)
    E = harness.ev_addr(g, 'build/Surfing.map')
    g.am.joy['up'] = 1; g.run(60); g.am.joy['up'] = 0
    g.am.joy['down'] = 1; g.run(50); g.am.joy['down'] = 0
    g.am.joy['up'] = 1; g.am.joy['fire'] = 1
    for i in range(80):
        g.run(1)
        if g.am.rb(E('air')) and s16(g.am.rw(E('avh'))) < 10: break
    g.shot('10_surfing')
elif w == 'skate':
    g = harness.event_game(6, out=OUT); g.idle(); g.run(40)
    E = harness.ev_addr(g, 'build/Skate.map')
    for i in range(600):
        air = g.am.rb(E('air'))
        g.am.joy['down'] = 0 if air else 1; g.am.joy['fire'] = 1 if air else 0
        g.run(2)
        if i > 200 and air and s16(g.am.rw(E('ay'))) < -40 * 16: break
    g.shot('11_skateboarding')
elif w == 'closing':
    g = harness.event_game(31, out=OUT); g.run(330); g.shot('12_closing')
