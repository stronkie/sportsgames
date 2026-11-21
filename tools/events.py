#!/usr/bin/env python3
"""events.py - the list of the 18 events of Stronkie's Olympics.  Writes build/gen/events.i for the main
program (names, files, units, how to play, the disk each one is on, the starting world records) and
build/gen/disks.txt for make_disk.py.  The disks are filled in the order of the events, after the event
files were built (build/full/*.evt).  Created By Mark Stronks, Stronkie Soft."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'gen')
FULL = os.path.join(ROOT, 'build', 'full')
PACKED = os.path.join(ROOT, 'build', 'packed')   # the crunched files of the floppy version (tools/crunch_all.py)

# name, file, unit, format (0 number, 1 time in 1/100 s, 2 distance in cm), lower is better, record (score, holder, country), how to play
EVENTS = [
 ('SOCCER', 'Soccer.evt', 'PTS', 0, 0, (9, 'G.GOALSBY', 13), [
  'PENALTY SHOOT-OUT AGAINST ANOTHER', 'COUNTRY: 5 SHOTS EACH, THEN SUDDEN', 'DEATH.', '',
  'SHOOTING: FIRE STOPS THE AIM, FIRE', 'AGAIN STOPS THE POWER (NOT OVER', 'THE BAR!)',
  'KEEPING: PUSH LEFT, RIGHT OR UP', 'JUST BEFORE THE KICK.', 'POINTS: GOALS + SAVES (+3 A WIN).']),
 ('BASKETBALL', 'Basket.evt', 'PTS', 0, 0, (25, 'D.DUNKWELL', 5), [
  'THREE POINT SHOOT-OUT: 5 RACKS OF 5', 'BALLS AND 60 SECONDS ON THE CLOCK.', '',
  'HOLD FIRE: THE POWER BAR GOES UP.', 'LET GO IN THE GREEN ZONE TO SCORE.', 'THE GREEN ZONE IS SMALLER FAR AWAY.', '',
  'THE LAST BALL OF A RACK (THE STRIPED', 'MONEY BALL) COUNTS 2 POINTS.']),
 ('VOLLEYBALL', 'Volley.evt', 'PTS', 0, 0, (16, 'S.SPIKER', 5), [
  'BEACH VOLLEYBALL AGAINST ANOTHER', 'COUNTRY: THE FIRST TO 7 POINTS WINS.', '',
  'LEFT/RIGHT: RUN.  FIRE: JUMP.', 'THE BALL BOUNCES OFF YOUR HANDS AND', 'HEAD. HIT IT HIGH IN A JUMP TO SPIKE.',
  "DON'T LET IT TOUCH THE SAND!", '', 'POINTS: 10 + YOUR POINTS - THEIRS.']),
 ('BOWLING', 'Bowling.evt', 'PINS', 0, 0, (268, 'E.STRIKE', 0), [
  'TEN PIN BOWLING: 10 FRAMES.', '', '1. LEFT/RIGHT: WHERE YOU STAND, FIRE.', '2. FIRE STOPS THE ARROW: THE SPIN.',
  '3. FIRE STOPS THE POWER BAR.', '', 'A STRIKE: ALL 10 PINS WITH ONE BALL.', 'A SPARE: ALL 10 WITH TWO BALLS.', 'THE BEST GAME IS 300.']),
 ('SURFING', 'Surfing.evt', 'PTS', 0, 0, (180, 'W.CURLER', 5), [
  'RIDE THE WAVE FOR 60 SECONDS.', '', 'LEFT/RIGHT/UP/DOWN: TURN THE BOARD.', 'RIDE DOWN FOR SPEED, RACE UP OFF THE',
  'TOP TO FLY: HOLD FIRE TO SPIN, LAND', 'POINTING DOWN THE WAVE.', 'POINTS FOR TURNS, AIRS AND SPINS AND',
  'FOR RIDING CLOSE TO THE CURL.', '3 WIPE-OUTS AND YOU ARE OUT!']),
 ('SKATEBOARDING', 'Skate.evt', 'PTS', 0, 0, (170, 'K.FLIPPER', 5), [
  'THE HALF PIPE: 60 SECONDS.', '', 'PUSH DOWN WHEN YOU ROLL THROUGH THE', 'BOTTOM TO GO FASTER AND HIGHER.',
  'IN THE AIR: PRESS FIRE TO TURN', 'AROUND (OR YOU FALL!).', 'UP IN THE AIR: A GRAB.  LEFT OR',
  'RIGHT: A SPIN.  HIGHER = MORE POINTS.', '3 FALLS AND YOU ARE OUT!']),
 ('100M SPRINT', 'Sprint.evt', 'S', 1, 1, (958, 'F.FLASH', 4), [
  '100 METRES AGAINST A RUNNER FROM', 'ANOTHER COUNTRY.', '',
  'WAIT FOR GO!  (A FALSE START AND YOU', 'START AGAIN)', '',
  'RUN: PUSH THE JOYSTICK LEFT, RIGHT,', 'LEFT, RIGHT... AS FAST AS YOU CAN.', '', 'THE FASTEST TIME WINS.']),
 ('HURDLES', 'Hurdles.evt', 'S', 1, 1, (1280, 'H.HOPPER', 4), [
  '110 METRES WITH 10 HURDLES.', '',
  'RUN: LEFT, RIGHT, LEFT, RIGHT...', 'JUMP: FIRE, JUST BEFORE A HURDLE.', '',
  'HIT A HURDLE AND YOU LOSE SPEED.', '', 'THE FASTEST TIME WINS.']),
 ('LONG JUMP', 'LongJump.evt', 'M', 2, 0, (895, 'L.LEAPER', 5), [
  'THREE JUMPS: THE BEST ONE COUNTS.', '', 'RUN: LEFT, RIGHT, LEFT, RIGHT...', 'AT THE WHITE BOARD: FIRE TO JUMP.', 'HOLD FIRE: THE ANGLE GOES UP.', 'LET GO AT ABOUT 45.', '', 'OVER THE BOARD IS A FOUL!', 'MORE SPEED = A LONGER JUMP.']),
 ('JAVELIN', 'Javelin.evt', 'M', 2, 0, (9848, 'S.SPEARS', 0), [
  'THREE THROWS: THE BEST ONE COUNTS.', '', 'RUN: LEFT, RIGHT, LEFT, RIGHT...', 'AT THE LINE: FIRE TO THROW.', 'HOLD FIRE: THE ANGLE GOES UP.', 'LET GO AT ABOUT 45.', '', 'OVER THE LINE IS A FOUL!', 'MORE SPEED = A LONGER THROW.']),
 ('ARCHERY', 'Archery.evt', 'PTS', 0, 0, (58, 'R.HOOD', 4), [
  'SIX ARROWS AT THE TARGET.', '',
  'MOVE THE SIGHT WITH THE JOYSTICK.', 'YOUR ARM SHAKES A LITTLE, AND WATCH', 'THE WIND!', '',
  'FIRE: SHOOT.  THE MIDDLE IS 10.', 'THE MOST POINTS WIN.']),
 ('SWIMMING', 'Swimming.evt', 'S', 1, 1, (2091, 'F.FINLEY', 5), [
  '50 METRES FREESTYLE.', '',
  'DIVE IN AT GO: FIRE.', 'SWIM: LEFT, RIGHT, LEFT, RIGHT...', 'YOUR AIR RUNS OUT: PRESS FIRE NOW AND', 'THEN TO BREATHE (WHEN THE BAR IS LOW).', '',
  'THE FASTEST TIME WINS.']),
 ('WEIGHTLIFTING', 'Weights.evt', 'KG', 0, 0, (264, 'I.IRONS', 15), [
  'THREE LIFTS, 30 KG MORE AFTER A', 'GOOD ONE.', '', 'LEFT, RIGHT, LEFT, RIGHT... FILLS THE', 'POWER BAR. OVER THE LINE? FIRE!', 'THEN ONCE MORE: OVER YOUR HEAD.', '', 'FIRE TOO SOON: NO LIFT.', 'THE HEAVIEST GOOD LIFT COUNTS.']),
 ('CYCLING', 'Cycling.evt', 'S', 1, 1, (3330, 'P.PEDALS', 4), [
  '500 METRES AGAINST THE CLOCK AND A', 'RIDER FROM ANOTHER COUNTRY.', '',
  'PEDAL: LEFT, RIGHT, LEFT, RIGHT...', 'UP/DOWN: A HIGHER/LOWER GEAR. A HIGH', 'GEAR IS FAST, BUT HEAVY WHEN SLOW.', '',
  'THE FASTEST TIME WINS.']),
 ('ROOT BEER SPRINT', 'RootBeer.evt', 'S', 1, 1, (1240, 'B.BURPER', 5), [
  "DRINK, RUN, DON'T HICCUP!", '', '1. HOLD FIRE TO DRINK YOUR MUG.', '   LET GO NOW AND THEN: THE HIC BAR', '   GOES UP WHILE YOU DRINK. FULL? HIC!', '', '2. EMPTY? RUN: LEFT, RIGHT...', '', 'THE FASTEST TIME WINS.']),
 ('PIE DODGE', 'PieDodge.evt', 'PTS', 0, 0, (90, 'S.CLEAN', 3), [
  'CROSS THE ARENA AS OFTEN AS YOU CAN', 'IN 60 SECONDS, WHILE THE CLOWNS', 'THROW PIES AT YOU!', '',
  'MOVE WITH THE JOYSTICK.', 'EVERY CROSSING: 10 POINTS.', 'A PIE IN YOUR FACE: -3, AND YOU', 'CAN\'T SEE FOR A MOMENT.']),
 ('PENGUIN CURLING', 'Curling.evt', 'PTS', 0, 0, (52, 'P.WADDLE', 10), [
  'CURLING WITH PENGUINS: SLIDE 6 OF', 'THEM TO THE MIDDLE OF THE HOUSE.', '', 'UP/DOWN: AIM, FIRE: THE POWER BAR.', 'FIRE AGAIN: SLIDE!', 'WHILE IT SLIDES: LEFT, RIGHT, LEFT,', 'RIGHT... SWEEP TO MAKE IT GO FURTHER.', '', 'CLOSE TO THE MIDDLE: MORE POINTS.']),
 ('TOILET PAPER THROW', 'TPThrow.evt', 'M', 2, 0, (3870, 'S.SOFTY', 6), [
  'THE JAVELIN, BUT WITH A TOILET ROLL!', 'THREE THROWS: THE BEST ONE COUNTS.', '',
  'RUN: LEFT, RIGHT, LEFT, RIGHT...', 'AT THE LINE: FIRE, HOLD FOR THE', 'ANGLE, LET GO AT ABOUT 45.', '',
  'WATCH THE WIND: IT CAN CARRY THE', 'ROLL A LONG WAY - OR NOT!']),
]
NCLASSIC = 14
REC_SIZE = 384

def blocks(n):
    d = max(1, math.ceil(n / 488))
    return d + 1 + (d - 1) // 72

def pack(sizes, first):
    """the event files in order onto disks of 1760 blocks -> disk number per event"""
    cap = 1760 - 12
    disk = 1; used = first; out = []
    for s in sizes:
        b = blocks(s)
        if used + b > cap: disk += 1; used = 6
        used += b; out.append(disk)
    return out

def asm_str(s):
    return "'" + s.replace("'", "',39,'") + "'"

def main():
    def size(f, guess):
        for d in (PACKED, FULL):
            if f != 'SOlymp' and os.path.exists(os.path.join(d, f)): return os.path.getsize(os.path.join(d, f))
        return guess
    sizes = [size(e[1], 60000) for e in EVENTS]
    first = blocks(size('SOlymp', 32000)) + blocks(size('SOlymp.game', 160000)) + blocks(size('Ceremony.evt', 60000))
    disks = pack(sizes, first + 8)
    L = ['; generated by tools/events.py', 'NEV\tequ\t%d' % len(EVENTS), 'NCLASSIC\tequ\t%d' % NCLASSIC, 'REC_SIZE\tequ\t%d' % REC_SIZE,
         'NDISKS\tequ\t%d' % max(disks)]
    D = ['; generated by tools/events.py: name, file, unit, how to play (.l), disk, format, lower is better, 0 (.w)', 'ev_tab']
    S = []
    for i, (n, f, u, fmt, low, rec, help) in enumerate(EVENTS):
        D.append('\tdc.l\tev_n%d,ev_f%d,ev_u%d,ev_h%d\n\tdc.w\t%d,%d,%d,0' % (i, i, i, i, disks[i], fmt, low))
        S.append('ev_n%d\tdc.b\t%s,0' % (i, asm_str(n)))
        S.append('ev_f%d\tdc.b\t%s,0' % (i, asm_str(f)))
        S.append('ev_u%d\tdc.b\t%s,0' % (i, asm_str(u)))
        S.append('ev_h%d\tdc.b\t%s,0' % (i, ',10,'.join(asm_str(h) if h else "' '" for h in help)))
    S.append('\teven')
    R = ["def_records\tdc.b\t'SOR2'"]
    for n, f, u, fmt, low, (sc, nm, ct), h in EVENTS:
        R.append('\tdc.l\t%d\n\tdc.b\t%s%s\n\tdc.w\t%d,0' % (sc, asm_str(nm), ',0' * (12 - len(nm)), ct))
    R.append('\tdcb.b\t%d,0\n\teven' % (REC_SIZE - 4 - 20 * len(EVENTS)))
    open(os.path.join(OUT, 'events_equ.i'), 'w').write('\n'.join(L) + '\n')
    open(os.path.join(OUT, 'events.i'), 'w').write('\n'.join(D + S + R) + '\n')
    with open(os.path.join(OUT, 'disks.txt'), 'w') as f:
        for e, d in zip(EVENTS, disks): f.write('%s %d\n' % (e[1], d))
    print('events: %d on %d disks: %s' % (len(EVENTS), max(disks), ' '.join(str(d) for d in disks)))

if __name__ == '__main__':
    main()
