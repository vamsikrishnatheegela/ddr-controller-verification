# DDR-Inspired Memory Controller — RTL & Verification

An educational SystemVerilog memory-controller model and open-source verification environment using **Verilator** and **Cocotb**.

> **Scope:** This is a simplified, DDR-inspired controller exercise. It is **not** a JEDEC-compliant DDR, DDR2, DDR3, DDR4, or DDR5 controller and does not implement a physical DRAM PHY, DFI, training, electrical timing, burst protocol, ECC, or refresh scheduling requirements of a real device.

## What is included

- A single-request-at-a-time controller FSM.
- Four logical banks and an internal behavioral memory model.
- ACTIVATE-like row opening, read/write access, and precharge/refresh sequencing.
- Parameterized simplified timing delays.
- Cocotb tests for reset, write/readback, multiple addresses, and refresh behavior.
- Verilator simulation via the Cocotb Makefile.

## Architecture

The 8-bit request address is divided into:
- `[7:6]`: bank (0–3)
- `[5:4]`: row (0–3)
- `[3:0]`: column (0–15)

The behavioral memory stores 256 bytes. A request is accepted when `req_valid && req_ready`. Write requests use `req_write=1`; read requests use `req_write=0`. A read returns a one-cycle `rsp_valid` pulse with `rsp_rdata`.

This is a functional teaching model; the simplified delays are cycle counts, not real DRAM nanoseconds.

## Tools

- SystemVerilog
- Verilator (timing support enabled)
- Python 3
- Cocotb 2.x

## Run simulation

On Ubuntu, install Verilator and Python tooling, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip cocotb
make
```

You can override the simulator with `SIM=icarus` if Icarus Verilog is installed, though Verilator is the documented default.

## Project layout

```text
rtl/ddr_controller.sv
tests/test_ddr_controller.py
Makefile
.gitignore
docs/verification_plan.md
```

## Verification status

The files provide the initial implementation and regression tests. Run `make` locally to produce the actual simulator result; a passing status should only be claimed after the regression has been run.

## Future extensions

1. Add protocol assertions and coverage counters.
2. Add randomized traffic and a reference-model scoreboard.
3. Model row-hit/row-miss latency and bank timing constraints more completely.
4. Add CI to run lint and simulation on each push.
5. Compare area/timing after synthesis with an appropriate open-source flow.

## License

MIT — see [LICENSE](LICENSE).
