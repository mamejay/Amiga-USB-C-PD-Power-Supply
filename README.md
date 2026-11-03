# Amiga USB-C PD Power Supply

A compact power supply that runs a Commodore **Amiga 500 / 600 / 1200** from a USB-C PD charger.
It asks the charger for **15 V** and makes the three Amiga rails on board:

| Rail | Converter | Set point | Rating | Protection |
|---|---|---|---|---|
| +5 V | TI TPS56637 6 A sync buck (FCCM) → TI TPS259470A eFuse | 5.10 V | **5 A continuous** (eFuse limit ~6 A typ, 5.3 A min) | eFuse cuts the output above **5.64 V** (failed buck can't reach the Amiga), current limit, ~5 ms soft start, SMF5.0A TVS, red fault LED |
| +12 V | TI LMR51430 3 A sync buck | 12.36 V | 2 A (floppy / RS-232 / audio / expansion) | cycle-by-cycle limit + hiccup, SMF13A TVS |
| −12 V | TI LMR51430 as inverting buck-boost (from +12 V) | −12.36 V | 0.5 A+ (Commodore PSU: 0.1 A) | hiccup limit, Schottky clamp against positive excursions, SMF13A TVS |

Input power budget is 45 W (15 V × 3 A), e.g. 5 V 5 A + 12 V 1 A + −12 V 0.2 A ≈ 39 W out.
The converters only start once the charger has agreed 15 V (CH224A power-good) **and** VBUS is above ~11.5 V,
so a 5 V-only or non-PD source never powers the Amiga.

## Charger / cable
* USB-C **PD** charger that offers **15 V at 3 A** (any 45 W+ PD charger; 65 W recommended).
* USB-C to USB-C cable rated 3 A or more (normal 60 W cables are fine).

## Board
* 64 × 46 mm, 2 layers, 1.6 mm, 1 oz. All SMD parts on the top side (JLCPCB economic PCBA).
* 4 × M3 mounting holes.
* **Cable pads (J2)**, 1.4 mm holes (up to 18 AWG), solder a ready-made Amiga square DIN-5 power cable:

  | J2 pad | Rail |
  |---|---|
  | 1, 2 | +5 V (use both, or one heavy wire) |
  | 3, 4 | GND (use both) |
  | 5 | +12 V |
  | 6 | −12 V |

  **Identify every wire of the DIN cable with a multimeter against the Amiga power socket pinout before soldering.**
  Cable wire colours are not standard between suppliers.

* LEDs: green +5 V, green +12 V, green −12 V, red = 5 V eFuse fault.

## Files
* `hw/` – KiCad 10 project (schematic, PCB, project symbol + footprint libraries, DRC/ERC reports).
* `fab/` – JLCPCB order files: Gerbers zip, BOM, CPL and `ORDER NOTES.md`.
* `scripts/` – the generators: `gen_sch.py` (schematic), `place.py` + `build_pcb.py` (placement/board),
  `full.sh` (net classes → Freerouting → pours → GND stitching → DRC loop), `make_fab.py`, `bom_cost.py`.
* `datasheets/` – not committed (vendor copyright); see the links in `docs/DESIGN.md`.

## Status
Rev 1.0 – designed, routed, ERC 0 / DRC 0 (only 2 cosmetic USB-C silk-at-edge marks), JLC files generated, **not yet built**.
Parts ≈ US$8.60 per board at 10 boards (JLC prices 2026-11-03), 7 extended parts. See `docs/DESIGN.md` for the calculations and the bring-up checklist.

## Licence
Copyright © 2026 mamejay. All rights reserved (commercial product). See `LICENSE` and `NOTICE.md`.
