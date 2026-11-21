# Pending itch.io release - Stronkie's Olympics

Mark publishes to itch.io on a fixed day of the week (Sunday), not after every build.
Everything that is built in between is collected here, so the next itch release shows every version.

**On itch now:** https://stronkie.itch.io/stronkies-olympics (edit: https://itch.io/game/edit/5407270): public, In development, paid 2.00€, with only the FREE DEMO (2 files: "DEMO (FREE) - Disk image ADF" and "DEMO (FREE) - WHDLoad"), cover, 11 screenshots. Published 20 November 2026 on request. The announcement devlog (itch/devlog.txt) was written but NOT posted: Mark posts it.
on request. The full game files (V0.1 ADFs, hard drive zip, WHDLoad) are NOT uploaded yet (Mark's wish).

## PUBLISHED 20 November 2026 (on Mark's request, not on a Sunday)
V0.2, V0.3 and V0.4 went to itch together: the full game V0.4 (3 ADFs in one zip + WHDLoad, paid at the page
price 2.00 EUR), the new demo, the print kit, new description, 14 new screenshots, new cover, status Released.
Devlog: https://stronkie.itch.io/stronkies-olympics/devlog/1793883/stronkies-olympics-is-out-18-events-national-anthems-and-the-amiga-look
(V0.5 followed on 21 November, see below.)

## Versions waiting to be published
(none)

## PUBLISHED 21 November 2026 (on Mark's request, not on a Sunday)
V0.5 went to itch: the full game on one crunched disk (ADF zip + WHDLoad, paid at the page price),
the crunched demo, the remade print kit (the V0.4 files are hidden on itch). Devlog:
https://stronkie.itch.io/stronkies-olympics/devlog/1795587/one-disk-stronkies-olympics-v05-the-whole-game-crunched-onto-one-floppy

## Published versions
### V0.6 - TEST VERSION - 21 November 2026 (bug fix; files on itch the same day, V0.5 files hidden)
- FIX: the game crashed (Software Failure 8000 0003) when a Soccer match ended - in the full game
  and in the free demo, since V0.1. The event kept its stack pointer among its variables and cleared
  them right after saving it, so it returned to address 0. All 18 events were played to the end in
  the test bench to check that no other event crashes on the way out

### V0.5 - TEST VERSION - 21 November 2026
- The whole game on ONE disk: all 18 events, both ceremonies, the anthems and the world records.
  No more disk swapping
- Our own cruncher (tools/crunch.py: LZ77, gamma codes, "same offset again" matches, optimal parse)
  packs every floppy file to about half its size: 1.75 MB of game -> 1729 of 1760 blocks
- Every hunk is unpacked in place while it loads (src/depack.s, in the loader and the kernel):
  no extra memory needed, still 512K + 512K. Faster loading from floppy: less than half as much
  is read, unpacking takes about a second per event on a 7 MHz 68000
- The free demo is crunched too; hard drive and WHDLoad versions stay unpacked (as fast as before)
- Manual, disk labels (now one GAME DISK label) and box remade for one disk; title screenshot shows V0.5
- Assembler and test bench learned ADDX/SUBX

### V0.4 - TEST VERSION - 20 November 2026
- New Amiga look for every screen: real stadium stands (roof, floodlights, rows of spectators,
  aisles) instead of coloured dots, sponsor boards, dithered grass, tracks, water, ice, sand and wood,
  copper colour gradients in the top bars, shaded athletes with eyes
- New screenshots; the print kit PDFs remade with them (re-upload them on the release day)

### V0.3 - TEST VERSION - 20 November 2026
- National anthems: at the medal ceremony you hear the anthem of the country that wins gold
  ("THE ANTHEM OF ..."), played once and quietly like the rest of the music. 17 of the 20 countries
  have their anthem; Norway, Brazil and Mexico still get the stadium fanfare
- All the anthem melodies are old enough to be free to use (the bass is our own)
- The print kit (free downloads, ALREADY ON ITCH since 20 November on request, with 2 new screenshots):
  print/StronkiesOlympics_Manual.pdf (24-page A5 booklet),
  print/StronkiesOlympics_DiskLabels.pdf (A4, colour + black and white) and print/StronkiesOlympics_Box.pdf
  (A3: the box to cut and fold, and the box in 3D)

### V0.2 - TEST VERSION - 20 November 2026
- 12 new events, 18 in all, each loaded from disk:
  - Classic: 100m Sprint, Hurdles, Long Jump, Javelin, Archery, Swimming, Weightlifting, Cycling
  - Silly: Root Beer Sprint (drink, run, don't hiccup), Pie Dodge, Penguin Curling, Toilet Paper Throw
- New menu choices: all 18 events, the 14 classic ones, the 4 silly ones, or choose
- Races against a rival from another country; field events with 3 attempts (the best counts)
- Times and distances in the results, the medal table and the world records (lower is better for times)
- New world record holders for every event; HOW TO PLAY for every event
- 3 disks now (the game asks for the disk it needs), hard drive zip, WHDLoad with all events
- The demo stays: the opening ceremony and Soccer
- Fixes: the WHDLoad ReadMe, leftover text in the message bar

### V0.1 - TEST VERSION - 20 November 2026
- The first version: six events (soccer, basketball, volleyball, bowling, surfing, skateboarding), each loaded
  from disk, make your own athlete, 1-4 players, medals, medal table, world records
- Opening and closing ceremony (Ceremony.evt), original music in the style of a stadium anthem
- 2 disks, hard drive zip, WHDLoad

## To do on the release day for the full game
1. Upload `StronkiesOlympics_V0.4_Disk1.adf` + `_Disk2.adf` + `_Disk3.adf` (or a zip with all three),
   `StronkiesOlympics_V0.4_harddrive.zip` and `whdload/StronkiesOlympics_V0.4_WHDLoad.lha` (paid, the page price).
   Keep the demo as the one free file. Do not name the GitHub repo anywhere (page, devlog, readmes).
2. Add the print kit when there is one, update the description, post a devlog and the announcement.
