# Rev 1.1: higher-capacity 5 V version (TPS56637, 5 A)

This is the same slim 76 × 32 mm board as rev 1.2, with the same cable pads, holes, +12 V and −12 V circuits. Only the 5 V converter is different:

| | Rev 1.1 (this folder) | Rev 1.2 (repo root) |
|---|---|---|
| 5 V buck | TI TPS56637 (6 A, VQFN-HR 3 × 3) | Silergy SY8205 (5 A, SO-8E) |
| L1 | CMLO0650H 3.3 µH | CMLO0650H 4.7 µH |
| eFuse current limit (ILM) | 560 Ω, about 6 A typ, 5.3 A min | 620 Ω, about 5.4 A typ, 4.8 A min |
| +5 V rating | **5 A continuous** | 4.5 A continuous (same as the Commodore A500 PSU) |
| Parts cost | about US$7.30 per board at 10 | about US$5.37 per board at 10 |

Choose rev 1.1 if you run a heavily expanded A500/A600/A1200 (accelerator, RAM, IDE/CF, Gotek and so on) on the 5 V rail.

## Files
* `hw/`: the KiCad 10 project (schematic, PCB, libraries, DRC/ERC reports).
* `fab/`: the JLCPCB files (Gerbers zip, BOM, CPL) and `ORDER NOTES.md`. The CPL already includes the JLC rotation fixes (U1, U4 and U5 at −90, Q1 at +180).
  For Economic PCBA, set the surface finish to HASL or LeadFree HASL, not OSP.
* `docs/`: `DESIGN.md` (rev 1.1 calculations and the bring-up checklist) and the renders.

The generator scripts for this revision are at git tag `v1.1`. The `scripts/` folder at the repo root builds rev 1.2.
