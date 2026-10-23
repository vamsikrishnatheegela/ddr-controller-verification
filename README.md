# DDR-Inspired Memory Controller — RTL & Verification

[![RTL Verification](https://github.com/vamsikrishnatheegela/ddr-controller-verification/actions/workflows/rtl-verification.yml/badge.svg)](https://github.com/vamsikrishnatheegela/ddr-controller-verification/actions/workflows/rtl-verification.yml)

An educational SystemVerilog memory-controller model and open-source verification environment using **Verilator** and **Cocotb**.

> **Scope:** This is a simplified, DDR-inspired controller exercise. It is **not** a JEDEC-compliant DDR, DDR2, DDR3, DDR4, or DDR5 controller and does not implement a physical DRAM PHY, DFI, training, electrical timing, burst protocol, ECC, or refresh scheduling requirements of a real device.

## What is included

- A single-request-at-a-time controller FSM.
- Four logical banks and an internal behavioral memory model.
- ACTIVATE-like row opening, read/write access, and precharge/refresh sequencing.
- Parameterized simplified timing delays.
- Cocotb directed tests and a Python reference-model scoreboard.
- Full 256-address write/readback sweep with bank/row/column coverage checks.
- Reset recovery, row-conflict, refresh collision, boundary-address, and data-isolation tests.
- GitHub Actions regression with downloadable simulation evidence.

## Architecture

The 8-bit request address is divided into:
- `[7:6]`: bank (0–3)
- `[5:4]`: row (0–3)
- `[3:0]`: column (0–15)

The behavioral memory stores 256 bytes. A request is accepted when `req_valid && req_ready`. Write requests use `req_write=1`; read requests use `req_write=0`. A read returns an `rsp_valid` pulse with `rsp_rdata`.

This is a functional teaching model; the simplified delays are cycle counts, not real DRAM nanoseconds.

## Tools

- SystemVerilog
- Verilator 5.036 or later
- Python 3
- Cocotb 2.1.x

## Run locally

On Ubuntu, install a compatible Verilator and Python tooling, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "cocotb>=2.1,<3"
make SIM=verilator
```

To capture a local text log and waveform (if supported by the simulator setup):

```bash
mkdir -p artifacts
set -o pipefail
make SIM=verilator WAVES=1 2>&1 | tee artifacts/regression.log
```

The regression writes Cocotb's JUnit-style `results.xml` as well. Generated logs, XML, waveforms, and build outputs should be treated as run-specific evidence rather than manually fabricated or edited.

## Project layout

```text
.github/workflows/rtl-verification.yml
rtl/ddr_controller.sv
tests/test_ddr_controller.py
Makefile
docs/verification_plan.md
```

## Verification evidence

Every push to `main`, pull request, or manual workflow dispatch triggers the GitHub Actions regression. The workflow records the commit SHA, tool versions, and simulator output, and uploads available logs, JUnit XML, waveform, and build files as a downloadable artifact retained for 90 days.

- **Workflow status and run history:** [RTL Verification on GitHub Actions](https://github.com/vamsikrishnatheegela/ddr-controller-verification/actions/workflows/rtl-verification.yml)
- **Test definitions and coverage checks:** [Cocotb testbench](tests/test_ddr_controller.py)
- **Test plan and evidence instructions:** [Verification plan](docs/verification_plan.md)

The earlier local baseline completed **6 tests with 6 passed, 0 failed, and 0 skipped**. The expanded suite now adds reset recovery, a full address-space sweep, and boundary/data-isolation checks. Its final pass status must be confirmed by the current regression run; see the linked workflow rather than assuming the expanded suite passed.

The checks are simulation evidence for the scenarios exercised. They do not prove formal correctness, physical PPA, silicon behavior, or JEDEC compliance.

## Future engineering work

- Add formal properties / assertion-based verification for stronger protocol guarantees.
- Expand FSM transition coverage and timing-parameter corner cases.
- Add synthesis and timing reports using a documented open-source flow.
- If claiming PPA, archive the exact tool versions, constraints, target library, and reports.

## License

MIT — see [LICENSE](LICENSE).
