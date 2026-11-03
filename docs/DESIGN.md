# Design notes – Amiga USB-C PD Power Supply rev 1.2

## Block diagram

```
USB-C ─┬─ CH224A (R1 56k = request 15 V) ── PG ──> Q1 2N7002 ──┐ holds EN low until the 15 V contract
       │                                                       │
 VBUS ─┼──── R3/R4 100k/12k ── EN ─────────────────────────────┤ (EN/UVLO: on ≥ ~11.5 V)
       │                                                       │
       ├── U2 SY8205 ─── L1 4.7 µH ── 5V_BUCK ── U3 TPS259470A eFuse ── +5 V ─┐
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
  | SY8205 (EN on 1.3 V, off 1.1–1.3 V) | 12.1 V | 10.3–12.1 V |
  | LMR51430 (1.227 V typ, 1.36 V max) | 11.5 V typ, 12.7 V max | 1.08 V → 10.1 V |

  With 15 V PD at −5 % (14.25 V) both still start in the worst case.
* No series input switch: VBUS carries 2×10 µF/50 V + 2×10 µF/25 V + 2×100 nF + 1 µF ≈ 30 µF effective at 5 V.
  That is above the USB Type-C 10 µF attach guideline, as on most PD trigger boards. Check this on the bring-up
  chargers (see the checklist).

### +5 V – U2 SY8205 (Silergy AN_SY8205), rev 1.2 cost-down from the TPS56637
* 5 A synchronous buck, 500 kHz, SO-8E. Bottom-FET current limit 5 A min, so the board is rated **4.5 A continuous**
  (the same as the original Commodore A500 supply).
* FB: 75 k / 10 k → 0.6 × 8.5 = 5.10 V, with 100 pF (C10) across R5 as the datasheet recommends for load steps.
* L1: CMLO0650H4R7MTT, 4.7 µH, 6.5 A rated / 8 A sat, 24 mΩ. The datasheet formula for 40 % ripple at 5 A from 15.75 V
  gives ≥ 3.4 µH. Ripple = 3.41 / (500 kHz × 4.7 µH) ≈ 1.45 A p-p, peak at 5 A ≈ 5.7 A < 8 A.
* COUT: 4 × 22 µF/25 V 0805 = 88 µF nominal (datasheet: > 47 µF X5R). CIN: 2 × 10 µF/50 V 1206 + 100 nF right at the IN pins.
* SS: 100 nF → 6 ms. VCC (internal 3.3 V LDO): 1 µF.
* EN: shared EN node; SY8205 rising threshold 1.3 V → starts at VBUS ≈ 12.1 V.

### 5 V eFuse – U3 TPS259470A
* OVLO: 100 k / 27 k → 1.20 V × 127/27 = **5.64 V trip**, 5.13 V release. If U2's high-side FET fails short,
  the Amiga sees at most 5.64 V for the OVLO response time, then 0 V. U3 is rated 23 V at IN, so it survives 15 V.
* ILM 620 Ω → about 5.4 A typ (4.8 A min, 5.85 A max), scaled from the datasheet table (549 Ω = 5.40 / 6.07 / 6.60 A,
  750 Ω = 3.96 / 4.45 / 4.84 A). The SY8205's own 5 A valley limit backs it up.
* dVdt 2.2 nF → ~0.9 V/ms (Eq. 4: C[pF] ≈ 2000 / SR[V/ms]), about 5.6 ms rise.
  A 1000 µF Amiga bulk cap then draws about 0.9 A of inrush.
* EN/UVLO 100 k / 47 k from 5V_BUCK: on above ~3.75 V. At 15 V fault input, EN stays at 4.8 V (< 5 V).
* FLT drives the red LED (D3) through R14 = 1 k from 5V_BUCK.

### +12 V – U4 LMR51430X (500 kHz, PFM)
* FB 100 k / 5.1 k → 12.36 V. TI Table 9-1 at 12 V: 12 µH, 3 × 22 µF.
* L2: FNR6045S120MT, 12 µH, 2.4 A rated / 3 A sat, 75 mΩ (6 × 6 mm; rev 1.0 used the 8 × 8 FNR8040). It carries the
  Amiga +12 V load plus the −12 V converter's input, about 1.1 A typical, so +12 V is rated 1.5 A continuous.
* Duty at 14.25 V = 0.87. With 150 ns minimum off-time at 500 kHz, about 92 % is available, so it regulates.

### −12 V – U5 LMR51430X inverting buck-boost, powered from +12 V
* The IC ground is the −12 V rail and the inductor (L3, 12 µH) returns to system GND.
* IC VIN − GND = 12.36 + 12.36 = 24.7 V (36 V max). CIN is 10 µF **50 V** (1206).
* D = 0.5. IL_avg = Iout / (1 − D) = 2 × Iout. Ripple = 12.36 × 0.5 / (12 µH × 500 kHz) ≈ 1.0 A p-p.
  L3 (FNR6045, 3 A sat) gives about 0.7 A of −12 V; the original Commodore PSU gives 0.1 A, and the Amiga needs < 0.1 A.
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
| SY8205FCC | C111875 | 5 V buck |
| TPS259470ARPWR | C3662799 | 5 V eFuse |
| LMR51430XDDCR | C5185863 | +12 V and −12 V (one part number) |
| CMLO0650H4R7MTT | C439009 | L1 |
| FCC0805X226M250FT | C7419435 | all 22 µF caps (cheaper than the Basic part even with the fee) |
| FNR6045S120MT | C168077 | L2 and L3 (one part number) |

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
4. Load test with electronic loads: 5 V at 4.5 A for 30 min, then 12 V at 1 A and −12 V at 0.2 A at the same time.
   Check U2, L1, U3 and U4 temperatures (U2 dissipates ~1.5 W and U3 ~0.6 W at 4.5 A).
5. eFuse: short +5 V (via a 1 Ω resistor first, then hard). U3 must limit and retry, and the red LED must light.
6. Only then connect the Amiga. **Meter the DIN cable pinout against the Amiga socket first.**

## Open items
* JLC CPL rotations were checked in JLC's 3D preview (rev 1.0, same footprints and rotations in rev 1.1): U1/U4/U5 −90,
  Q1 +180, in `scripts/make_fab.py` `JLC_ROT_FIX`.
* U2 (SY8205, SO-8E) is new in rev 1.2: check its rotation in JLC's preview (pin 1 = BS, bottom-right in the board view).
* Case: not designed yet. Board 76 × 32 mm; the four M3 holes are at (3.5, 3.5), (3.5, 28.5), (72.5, 3.5), (72.5, 28.5) mm
  from the board's top-left corner.
