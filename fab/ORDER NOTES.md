# JLCPCB order notes – Amiga USB-C PD Power Supply rev 1.1

## PCB
* Upload `Amiga USB-C PD Power Supply - Gerbers.zip`.
* 2 layers, 76 × 32 mm, 1.6 mm FR-4, **1 oz** outer copper (2 oz is optional and gives more current headroom
  but is not needed), HASL lead-free or ENIG, any mask colour.
* Remove order number: "Specify a location" is not set up, so choose "Remove" (paid) or leave it as is.

## Assembly (PCBA)
* **Economic**, **top side only**. Upload `... - BOM.csv` and `... - CPL.csv`.
* 66 placements, 32 BOM lines. Extended parts (about $3 each per order): CH224A, USB-C C165948, TPS56637,
  TPS259470A, LMR51430 (U4 + U5), CMLO0650H3R3 (L1), FNR6045S120 (L2 + L3). Everything else is Basic or Preferred.
* Rotations checked in the JLC preview 2026-11-03 (U1/U4/U5 −90, Q1 +180 are in the CPL). Still glance at the preview: U1, U2 (VQFN-HR), U3, U4/U5 – compare each pin 1 with the
  KiCad board (`hw/`, F.Fab layer) – D1–D8 (cathode band / LED polarity), Q1, J1 (opening to
  the board edge). Note any fix in `scripts/make_fab.py` `JLC_ROT_FIX` for next time.
* J2 (cable pads) and the M3 holes are not assembled.

## After delivery
Follow the bring-up checklist in `docs/DESIGN.md` **before** connecting an Amiga.
