# Verification Plan

## Scope

Verify the simplified educational controller behavior. These checks do not establish JEDEC DDR protocol compliance.

## Directed tests

1. **Write/readback:** write a byte to an address and read the same address back.
2. **Bank/address coverage:** write/read addresses mapping to each of the four logical banks.
3. **Refresh:** request refresh after a transaction; check that refresh completes and stored behavioral memory persists.
4. **Row conflict:** access different rows in the same bank and verify previously written addresses remain intact.
5. **Refresh/request collision:** present a request while refresh is requested; verify `req_ready` is low and the unaccepted write has no effect.
6. **Reference scoreboard:** compare a deterministic mixed sequence of reads and writes against a Python memory model.

## Interface expectations

- Requests are accepted only while `req_ready` is high.
- A write is accepted with `req_valid=1` and `req_write=1`.
- A read produces `rsp_valid=1` for one cycle and presents data on `rsp_rdata`.
- Refresh is requested with `refresh_req=1`; the controller completes using a one-cycle `refresh_done` pulse.

## Run

```bash
make SIM=verilator
```

## Planned additions

- Assertions for legal state transitions and response timing.
- Constrained-random read/write traffic and broader reference-model checking.
- Functional coverage for bank, row, column, row hit, row conflict, refresh from closed/open banks.
- CI using a pinned toolchain.
