# Design notes – Amiga USB-C PD Power Supply rev 1.0

## Block diagram

```
USB-C ─┬─ CH224A (R1 56k = request 15 V) ── PG ──> Q1 2N7002 ──┐ holds EN low until the 15 V contract
       │                                                       │
 VBUS ─┼──── R3/R4 100k/12k ── EN ─────────────────────────────┤ (EN/UVLO: on ≥ ~11.5 V)
       │                                                       │
       ├── U2 TPS56637 ── L1 3.3 µH ── 5V_BUCK ── U3 TPS259470A eFuse ── +5 V ─┐
       └── U4 LMR51430 ── L2 12 µH ── +12 V ──────────────────────────────────┤──> J2 cable pads
                           └── U5 LMR51430 inverting ── L3 12 µH ── −12 V ────┘
```

## Rails

### Input
* CH224A, CFG1 = 56 kΩ → 15 V request (same configuration as the working C64 adapter v0.3).
* Run control: the CH224A PG pin is open drain and 32 V tolerant. Until the PD contract is made, PG floats, R2 pulls
  Q1's gate to VBUS, and Q1 holds EN low. When PG goes low, Q1 turns off and EN rises to VBUS × 12/112 = 1.6 V at 15 V.
* EN/UVLO (shared by U2 and U4):

  | Part | Start | Stop |
  |---|---|---|
  | TPS56637 (EN on 1.18 V typ) | 11.0 V | 1.04–1.12 V → 9.7–10.5 V |
  | LMR51430 (1.227 V typ, 1.36 V max) | 11.5 V typ, 12.7 V max | 1.08 V → 10.1 V |

  With 15 V PD at −5 % (14.25 V) both still start in the worst case.
* No series input switch: VBUS carries 2×10 µF/50 V + 2×10 µF/25 V + 2×100 nF + 1 µF ≈ 30 µF effective at 5 V.
  That is above the USB Type-C 10 µF attach guideline, as on most PD trigger boards. Check this on the bring-up
  chargers (see the checklist).

### +5 V – U2 TPS56637 (datasheet SLVSEG1A, Table 4 "5 V" row)
* FB: 75 k / 10 k → 0.6 × 8.5 = 5.10 V. Feed-forward: 100 pF + 20 k (TI: 100–220 pF + 20 k).
* L1: 3.3 µH (TI table), CMLO0650H3R3MTT, 8.5 A rated / 9 A sat, 14 mΩ.
  Ripple at 15 V in: (15 − 5.1) × 0.34 / (3.3 µH × 500 kHz) ≈ 2.0 A p-p. Peak at 6 A ≈ 7 A < 9 A.
* COUT: 4 × 22 µF/25 V 0805 ≈ 40 µF effective at 5 V (TI: 20–100 µF).
  CIN: 2 × 10 µF/50 V 1206 + 100 nF. The 1206 parts keep about 6 µF each at 15 V.
* MODE floating = FCCM (fixed frequency, no audible light-load bursts).
* Valley current limit 6.3 A min, so the eFuse (≤ 6.47 A) is always the limiting element.

### 5 V eFuse – U3 TPS259470A
* OVLO: 100 k / 27 k → 1.20 V × 127/27 = **5.64 V trip**, 5.13 V release. If U2's high-side FET fails short,
  the Amiga sees at most 5.64 V for the OVLO response time, then 0 V. U3 is rated 23 V at IN, so it survives 15 V.
* ILM 560 Ω → about 5.95 A typ (5.3 A min). The datasheet table gives 549 Ω = 5.40 / 6.07 / 6.60 A (min / typ / max).
* dVdt 2.2 nF → ~0.9 V/ms (Eq. 4: C[pF] ≈ 2000 / SR[V/ms]), about 5.6 ms rise.
  A 1000 µF Amiga bulk cap then draws about 0.9 A of inrush.
* EN/UVLO 100 k / 47 k from 5V_BUCK: on above ~3.75 V. At 15 V fault input, EN stays at 4.8 V (< 5 V).
* FLT drives the red LED (D3) through R14 = 1 k from 5V_BUCK.

### +12 V – U4 LMR51430X (500 kHz, PFM)
* FB 100 k / 5.1 k → 12.36 V. TI Table 9-1 at 12 V: 12 µH, 3 × 22 µF.
* L2: FNR8040S120MT, 12 µH, 3 A / 4 A sat.
* Duty at 14.25 V = 0.87. With 150 ns minimum off-time at 500 kHz, about 92 % is available, so it regulates.

### −12 V – U5 LMR51430X inverting buck-boost, powered from +12 V
* The IC ground is the −12 V rail and the inductor (L3, 12 µH) returns to system GND.
* IC VIN − GND = 12.36 + 12.36 = 24.7 V (36 V max). CIN is 10 µF **50 V** (1206).
* D = 0.5. IL_avg = Iout / (1 − D) = 2 × Iout. Ripple = 12.36 × 0.5 / (12 µH × 500 kHz) ≈ 1.0 A p-p.
  The high-side limit is 3.67 A min, so roughly 1.3 A of −12 V is possible. The Amiga needs < 0.1 A.
* RHP zero ≈ (1 − D)² × R / (2π × D × L) ≈ 200 kHz at 0.5 A, well above the internal loop crossover.
* EN: 100 k / 20 k from +12 V to −12 V: 2.06 V at start, 4.1 V running.
* D6 (B5819W, anode −12 V, cathode GND) stops the rail from being dragged positive at start-up and power-down.

## JLCPCB parts

Passives are all **Basic**. The two SMF TVS parts are **Preferred**, so they have no feeder fee.

The **extended** parts below each cost about $3 per order:

| Part | LCSC | Use |
|---|---|---|
| CH224A | C42459160 | PD sink |
| HRO TYPE-C-31-M-12 | C165948 | USB-C |
| TPS56637RPAR | C841386 | 5 V buck |
| TPS259470ARPWR | C3662799 | 5 V eFuse |
| LMR51430XDDCR | C5185863 | +12 V and −12 V (one part number) |
| CMLO0650H3R3MTT | C439008 | L1 |
| FNR8040S120MT | C168128 | L2 and L3 (one part number) |

Run `scripts/bom_cost.py "fab/Amiga USB-C PD Power Supply - BOM.csv" <boards>` for current stock and prices.

## Bring-up checklist (first boards)

1. **No load, bench supply first.** Feed 15 V to VBUS (test pads C2/C3) with a 0.5 A current limit and check:
   * 5V_BUCK ≈ 5.10 V, +5 V (after the eFuse) ≈ 5.10 V;
   * +12 V ≈ 12.36 V, −12 V ≈ −12.36 V;
   * all three green LEDs on, red LED off.
2. Drop the supply to 9 V: all rails must be off. Then 12 V: rails may run (that is the UVLO window, by design).
   With USB PD, PG gating keeps them off below 15 V.
3. USB-C chargers: test several (Apple, Anker, UGREEN, a cheap one). Confirm the 15 V contract on a USB-C meter
   and that no charger trips at attach (input capacitance note above).
4. Load test with electronic loads: 5 V at 5 A for 30 min, then 12 V at 1 A and −12 V at 0.2 A at the same time.
   Check U2, L1, U3 and U4 temperatures (U3 dissipates ~0.7 W at 5 A).
5. eFuse: short +5 V (via a 1 Ω resistor first, then hard). U3 must limit and retry, and the red LED must light.
6. Only then connect the Amiga. **Meter the DIN cable pinout against the Amiga socket first.**

## Open items
* JLC CPL rotations: check every IC, the diodes, the LEDs and J1 in JLC's 3D preview before ordering, and record the
  offsets in `scripts/make_fab.py` (`JLC_ROT_FIX`).
* The TPS56637 RPA land pattern comes from EasyEDA (LCSC C841386). Compare it with TI's RPA0010A drawing before the first order.
* Case: not designed yet. The four M3 holes are at (4, 3.5), (4, 42.5), (60.5, 4), (60.5, 42) mm from the board's top-left corner.
