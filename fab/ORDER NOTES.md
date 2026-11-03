# JLCPCB order notes – Amiga USB-C PD Power Supply rev 1.2

## PCB
* Upload `Amiga USB-C PD Power Supply - Gerbers.zip`.
* 2 layers, 76 × 32 mm, 1.6 mm FR-4, **1 oz** outer copper.
* **To get Economic PCBA:** colour **Green** (or Black), Surface Finish **LeadFree HASL** or **HASL(with lead)** (ENIG
  green only). **Not OSP**: JLC's new OSP option is Standard-only and was why the first quote was Standard (2026-11-03).
  Delivery format Single PCB, PCB qty 2–50, every high-spec / special option left at its default.
* Remove order number: "Specify a location" is not set up, so choose "Remove" (paid) or leave it as is.

## Assembly (PCBA)
* **Economic**, **top side only**. Upload `... - BOM.csv` and `... - CPL.csv`.
* 67 placements, 32 BOM lines. Extended parts (about $3 each per order): CH224A, USB-C C165948, SY8205FCC,
  TPS259470A, LMR51430 (U4 + U5), CMLO0650H4R7 (L1), FNR6045S120 (L2 + L3), Fojan 22 µF C7419435. Everything else is Basic or Preferred.
* Rotations checked in the JLC preview 2026-11-03 (U1/U4/U5 −90, Q1 +180 are in the CPL). **U2 is a new part (SY8205, SO-8E) – check its pin 1 (BS) in the preview.** Also glance at U1, U3, U4/U5 – compare each pin 1 with the
  KiCad board (`hw/`, F.Fab layer) – D1–D8 (cathode band / LED polarity), Q1, J1 (opening to
  the board edge). Note any fix in `scripts/make_fab.py` `JLC_ROT_FIX` for next time.
* J2 (cable pads) and the M3 holes are not assembled.

## After delivery
Follow the bring-up checklist in `docs/DESIGN.md` **before** connecting an Amiga.
