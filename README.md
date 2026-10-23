# DDR-Inspired Memory Controller — RTL Design & Functional Verification

[![RTL Verification](https://github.com/vamsikrishnatheegela/ddr-controller-verification/actions/workflows/rtl-verification.yml/badge.svg)](https://github.com/vamsikrishnatheegela/ddr-controller-verification/actions/workflows/rtl-verification.yml)

An educational **SystemVerilog memory-controller RTL model** with a Python-based **Cocotb verification environment**, compiled and simulated using **Verilator**. The project demonstrates RTL control logic, transaction-level testbench development, scoreboard checking, functional-coverage closure, continuous integration, and waveform-based debugging.

> **Scope and limitations:** This is a simplified, DDR-inspired educational controller. It is **not** a JEDEC-compliant DDR, DDR2, DDR3, DDR4, or DDR5 controller. It does not implement a physical DRAM PHY, DFI, training/calibration, electrical timing, real DDR burst protocol, ECC, or the full refresh and scheduling requirements of commercial DRAM devices.

## Project status

**Current milestone: complete.** The defined local regression passed all 10 tests, functional-coverage goals passed, the GitHub Actions regression passed, and simulation waveform inspection was completed. Further work is optional enhancement, not a blocker for describing this version as completed.

| Milestone | Result |
|---|---|
| SystemVerilog RTL controller | Complete |
| Cocotb regression suite | **10/10 tests passed** in the recorded local run |
| Functional coverage closure | Passed |
| Address-space sweep | **256/256 addresses** exercised |
| Bank/row/column coverage | **4/4 banks, 4/4 rows, 16/16 columns** |
| Read/write × bank coverage | **8/8 bins** |
| GitHub Actions CI | Passed in the recorded run |
| Waveform generation and inspection | Completed using GTKWave |
| Functional-coverage changes | Merged into `main` (PR #1) |

These results apply to the defined tests and coverage goals; they are not a formal proof of correctness, JEDEC compliance, physical performance, or silicon behavior. Check the latest workflow run for current CI status.

## Key features

- Single-request-at-a-time controller FSM.
- Four logical banks and an internal behavioral memory model.
- Row opening, access, precharge-like behavior, and refresh sequencing.
- Simplified programmable/cycle-based timing parameters.
- Read and write transaction handling with request/response handshake signals.
- Active-low asynchronous reset and reset-recovery testing.
- Row-conflict handling and request blocking during refresh.
- Cocotb tests, Python reference-model scoreboard, and a functional-coverage collector.
- Full 256-address write/readback sweep.
- Automated GitHub Actions regression and downloadable verification evidence.

## Architecture

### Address mapping

The 8-bit request address is divided into bank, row, and column fields:

| Address bits | Field | Range |
|---|---|---|
| `[7:6]` | Bank | 0–3 (4 banks) |
| `[5:4]` | Row | 0–3 (4 rows per bank) |
| `[3:0]` | Column | 0–15 (16 columns per row) |

The behavioral memory contains 256 bytes in total. This address mapping is deliberately small so that the complete address space can be swept in simulation.

### Request/response interface

- `req_valid`: requester indicates a transaction is available.
- `req_ready`: controller indicates it can accept a transaction.
- A request is accepted when `req_valid && req_ready` is true.
- `req_write=1`: write request; `req_write=0`: read request.
- `req_addr[7:0]`: 8-bit address.
- `req_wdata[7:0]`: 8-bit write data.
- `rsp_valid`: response-valid indication.
- `rsp_rdata[7:0]`: 8-bit read data.
- `refresh_req` / `refresh_done`: refresh request and completion signals.
- `clk` and active-low asynchronous `rst_n`: clock and reset.

### Controller state machine

The RTL models these states:

1. `ST_IDLE` — wait for a request or refresh activity.
2. `ST_PRECHARGE` — close/precharge a conflicting open row.
3. `ST_ACTIVATE` — open the target row.
4. `ST_RCD_WAIT` — wait the simplified row-to-column delay.
5. `ST_ACCESS` — perform the behavioral read/write access.
6. `ST_RESPONSE` — return transaction response.
7. `ST_REFRESH_PRE` — prepare banks for refresh.
8. `ST_REFRESH_WAIT` — wait the simplified refresh interval.

The RTL includes timing parameters such as `MAX_DELAY`, `TIMER_W`, `T_RCD`, `T_RFC`, and `T_RP`. In this educational model, timing values represent simulation-cycle counts, not real DRAM timing in nanoseconds.

## Verification methodology

The testbench is written in Python using Cocotb. It drives the controller interface, observes responses, checks transaction results, and uses a reference-model scoreboard for deterministic mixed traffic. A functional-coverage collector tracks whether selected behaviors and address dimensions have been exercised.

### Test scenarios

The 10-test regression includes:

1. Write/readback behavior.
2. Access across multiple banks.
3. Refresh closes rows and completes.
4. Row-conflict behavior preserves data at each address.
5. Request is not accepted during refresh.
6. Deterministic mixed traffic checked with a scoreboard.
7. Reset clears controller and behavioral memory state.
8. Full address-space sweep.
9. Consecutive transactions keep data isolated.
10. Functional-coverage closure.

### Functional coverage goals

The coverage collector checks:

- **Address space:** 256/256 addresses.
- **Address dimensions:** 4/4 banks, 4/4 rows, and 16/16 columns.
- **Operations:** read and write.
- **Cross coverage:** 8/8 operation-by-bank bins.
- **Write-data classes:** zero, all-ones, alternating patterns (including `0x55`/`0xAA`), and other values.
- **Refresh:** minimum request and completion event goals.
- **Reset:** reset-event goal.

Coverage closure is based on these explicitly defined bins and event goals. It should not be interpreted as exhaustive functional or formal coverage of all possible RTL behaviors.

## Simulation waveform and debugging

A simulation waveform was generated and inspected in **GTKWave**. The capture includes the main interface signals and internal control/debug signals, including:

- Clock and active-low reset: `clk`, `rst_n`.
- Request/response handshake: `req_valid`, `req_ready`, `rsp_valid`.
- Transaction controls and data: `req_write`, `req_addr`, `req_wdata`, `rsp_rdata`.
- Refresh controls: `refresh_req`, `refresh_done`.
- Bank/row tracking: `bank_open`, `open_row[]`.
- Saved transaction context: `saved_addr`, `saved_bank`, `saved_row`, `saved_wdata`, `saved_write`.
- Controller progress: `state`, `timer`, and timing parameters.

Waveform inspection is useful for correlating request acceptance with FSM transitions, timer progression, bank/row tracking, and response activity. The waveform is a debugging artifact and does not by itself establish protocol compliance or performance.

To generate a local waveform where supported by the installed Cocotb/Verilator setup:

```bash
make clean
make SIM=verilator WAVES=1
find . -type f \( -name "*.vcd" -o -name "*.fst" \) -print
```

Open the resulting VCD/FST file in GTKWave. Generated waveform and build files are run-specific; do not commit generated outputs unless you deliberately intend to version a small, documented evidence capture.

## Tools and technologies

- **RTL:** SystemVerilog
- **Testbench:** Python, Cocotb 2.1.x
- **Simulator:** Verilator 5.036 or later
- **Waveform viewer:** GTKWave
- **Automation/build:** Make, Git, GitHub Actions
- **Verification concepts:** FSM-based control, request/response handshakes, directed testing, deterministic mixed traffic, reference-model scoreboard, functional coverage, regression logging, waveform debugging

## Run locally

On Ubuntu, use a compatible Verilator installation and Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "cocotb>=2.1,<3"
make SIM=verilator
```

To save the regression output:

```bash
mkdir -p artifacts
set -o pipefail
make SIM=verilator WAVES=1 2>&1 | tee artifacts/regression.log
```

The Cocotb regression also writes JUnit-style `results.xml`. Exact waveform location and generation depend on the installed simulator build and tracing configuration.

## Continuous integration and evidence

Every push to `main`, pull request, or manual workflow dispatch triggers the GitHub Actions verification workflow. It records the commit SHA and tool versions, runs the regression, and uploads available regression logs, JUnit XML, waveform/build outputs as a downloadable artifact.

- **[RTL Verification workflow and run history](https://github.com/vamsikrishnatheegela/ddr-controller-verification/actions/workflows/rtl-verification.yml)**
- **[Cocotb testbench](tests/test_ddr_controller.py)**
- **[Verification plan](docs/verification_plan.md)**

The workflow artifact is the best place to retrieve evidence associated with a particular CI commit. The waveform screenshot inspected locally is not automatically embedded in this README; it must be committed as a separate image file if a rendered screenshot is desired on the repository page.

## Applications and relevance

This project demonstrates foundational techniques applicable to:

- RTL design and verification of memory-interface IP.
- SoC peripheral and embedded-system controller blocks.
- Behavioral memory and SRAM/BRAM controller exercises.
- Pre-silicon functional validation and regression automation.
- Debugging FSM-based control logic using waveform traces.
- Verification environments built around scoreboards and functional coverage.

These are skill-transfer and learning applications. The current RTL is not suitable for direct use as a commercial DDR controller.

## Future engineering enhancements

The current milestone is complete. Potential extensions include:

- Add SystemVerilog Assertions (SVA) for handshake, response, reset, and refresh properties.
- Add constrained-random traffic and reproducible seeds.
- Measure request latency, sustained throughput, and refresh overhead.
- Increase FSM transition and corner-case coverage.
- Parameterize address geometry and timing, then test parameter boundaries.
- Add lint and formal-property checks.
- Explore synthesis/timing reports using a documented flow and explicit constraints.
- Develop a more realistic protocol model if the goal is to study JEDEC DDR behavior.

If reporting PPA or performance figures, include the exact tool versions, constraints, target library, measurement method, and reports. No PPA or JEDEC-compliance claim is made for the current project.

## Project layout

```text
.github/workflows/rtl-verification.yml
rtl/ddr_controller.sv
tests/test_ddr_controller.py
Makefile
docs/verification_plan.md
```

## License

MIT — see [LICENSE](LICENSE).
