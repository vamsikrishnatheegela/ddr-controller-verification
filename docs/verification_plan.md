# Verification Plan

## Scope

Verify the simplified educational controller behavior. These checks do not establish JEDEC DDR protocol compliance. The testbench uses Cocotb, a Python functional-coverage collector, and a Python reference model with Verilator.

## Directed and regression tests

1. **Write/readback:** write a byte to an address and read the same address back.
2. **Bank/address coverage:** write/read addresses mapping to each of the four logical banks.
3. **Refresh:** request refresh after a transaction; check that refresh completes and stored behavioral memory persists.
4. **Row conflict:** access different rows in the same bank and verify previously written addresses remain intact.
5. **Refresh/request collision:** present a request while refresh is requested; verify req_ready is low and the unaccepted write has no effect.
6. **Reference scoreboard:** compare a deterministic mixed sequence of reads and writes against a Python memory model.
7. **Reset recovery:** assert asynchronous reset while the controller is busy; verify idle/response outputs and that behavioral memory is cleared.
8. **Full address-space sweep:** write and read back all 256 addresses; assert coverage of all 4 banks, 4 rows, and 16 columns.
9. **Data isolation / boundaries:** exercise addresses 0x00 and 0xFF and alternating data patterns, then read in reverse order.
10. **Functional coverage closure:** report accumulated coverage and fail the regression if the configured coverage goals are not met.

## Functional coverage model

The collector samples each request driven through the common `transact()` helper and aggregates coverage across the regression.

| Coverage point | Goal |
|---|---:|
| Unique addresses | 256/256 |
| Logical banks | 4/4 |
| Row indices | 4/4 |
| Column indices | 16/16 |
| Operations | read + write |
| Operation × bank cross | 8/8 bins |
| Write data classes | zero, all-ones, alternating, other |
| Refresh requests | at least 2 |
| Refresh completions | at least 2 |
| Reset events | at least 1 |

The collector emits a `FUNCTIONAL COVERAGE SUMMARY` line and the closure test asserts each configured goal. These are address-map and transaction coverage points, not complete FSM transition coverage, assertion-based protocol verification, or JEDEC timing coverage.

## Interface expectations checked

- Requests are accepted only while req_ready is high.
- A write is accepted with req_valid=1 and req_write=1.
- A read produces an rsp_valid pulse and presents data on rsp_rdata.
- Refresh is requested with refresh_req=1; the controller completes using a refresh_done pulse.
- Reset returns the controller to its initial state and clears the modeled memory.

## Run locally

```bash
source .venv/bin/activate
make SIM=verilator
```

To generate a waveform when supported by the installed Cocotb/Verilator combination:

```bash
make SIM=verilator WAVES=1
```

To retain a plain-text proof log locally:

```bash
mkdir -p artifacts
set -o pipefail
make SIM=verilator WAVES=1 2>&1 | tee artifacts/regression.log
```

## Continuous integration and evidence

The GitHub Actions workflow at .github/workflows/rtl-verification.yml runs the regression on pushes to main, pull requests, and manual dispatch. It captures the tool versions and simulation output and uploads available regression.log, results.xml, waveform, and simulator build files as a downloadable artifact (90-day retention).

A CI pass is evidence that the checked-in regression passed in that runner environment. It is not proof of formal correctness, silicon behavior, physical PPA, or JEDEC compliance.
