import cocotb
from cocotb.triggers import RisingEdge, Timer


async def cycle(dut, count=1):
    for _ in range(count):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")


async def reset_dut(dut):
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.req_valid.value = 0
    dut.req_write.value = 0
    dut.req_addr.value = 0
    dut.req_wdata.value = 0
    dut.refresh_req.value = 0
    # Run a simple manual clock for reset, then use the background clock below.
    await Timer(2, unit="ns")
    dut.clk.value = 1
    await Timer(2, unit="ns")
    dut.clk.value = 0
    dut.rst_n.value = 1
    await Timer(1, unit="ns")


async def pulse_clock(dut):
    dut.clk.value = 0
    while True:
        await Timer(5, unit="ns")
        dut.clk.value = 1
        await Timer(5, unit="ns")
        dut.clk.value = 0


async def transact(dut, write, addr, data=0):
    # Wait until controller advertises request readiness.
    for _ in range(100):
        if int(dut.req_ready.value):
            break
        await cycle(dut)
    else:
        raise AssertionError("Controller did not become ready")

    dut.req_addr.value = addr
    dut.req_wdata.value = data
    dut.req_write.value = int(write)
    dut.req_valid.value = 1
    await cycle(dut)
    dut.req_valid.value = 0

    for _ in range(100):
        await cycle(dut)
        if int(dut.rsp_valid.value):
            return int(dut.rsp_rdata.value)
        if write and int(dut.req_ready.value):
            return None
    raise AssertionError("Transaction timed out")


@cocotb.test()
async def write_then_readback(dut):
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)

    await transact(dut, True, 0x21, 0xA5)
    result = await transact(dut, False, 0x21)
    assert result == 0xA5, f"Expected 0xA5, got {result!r}"


@cocotb.test()
async def multiple_banks_and_addresses(dut):
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)

    vectors = [(0x01, 0x12), (0x41, 0x34), (0x82, 0x56), (0xC3, 0x78)]
    for addr, data in vectors:
        await transact(dut, True, addr, data)
    for addr, data in vectors:
        result = await transact(dut, False, addr)
        assert result == data, f"Address 0x{addr:02X}: expected 0x{data:02X}, got {result!r}"


@cocotb.test()
async def refresh_closes_rows_and_completes(dut):
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)
    await transact(dut, True, 0x20, 0x5A)

    dut.refresh_req.value = 1
    await cycle(dut)
    dut.refresh_req.value = 0
    for _ in range(30):
        await cycle(dut)
        if int(dut.refresh_done.value):
            break
    else:
        raise AssertionError("refresh_done was not asserted")

    result = await transact(dut, False, 0x20)
    assert result == 0x5A, f"Data should persist across refresh; got {result!r}"



@cocotb.test()
async def row_conflict_preserves_each_address(dut):
    """Access two rows in one bank and verify precharge/activate handling."""
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)

    # Same bank (address[7:6] == 0), different rows (address[5:4]).
    vectors = [(0x01, 0x11), (0x21, 0x22), (0x31, 0x33), (0x01, 0x44)]
    for addr, data in vectors:
        await transact(dut, True, addr, data)

    # The last write overwrites 0x01; other row data must remain intact.
    expected = [(0x01, 0x44), (0x21, 0x22), (0x31, 0x33)]
    for addr, data in expected:
        result = await transact(dut, False, addr)
        assert result == data, (
            f"Address 0x{addr:02X}: expected 0x{data:02X}, got {result!r}"
        )


@cocotb.test()
async def request_is_not_accepted_during_refresh(dut):
    """A request presented with refresh must wait rather than be lost as accepted."""
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)

    dut.refresh_req.value = 1
    dut.req_valid.value = 1
    dut.req_write.value = 1
    dut.req_addr.value = 0x52
    dut.req_wdata.value = 0xD7
    await Timer(1, unit="ns")
    assert int(dut.req_ready.value) == 0, "req_ready must be low during refresh request"

    await cycle(dut)
    dut.refresh_req.value = 0
    dut.req_valid.value = 0

    for _ in range(30):
        await cycle(dut)
        if int(dut.refresh_done.value):
            break
    else:
        raise AssertionError("refresh did not complete")

    # The unaccepted write must not have modified memory.
    result = await transact(dut, False, 0x52)
    assert result == 0, f"Unaccepted write unexpectedly changed memory to 0x{result:02X}"


@cocotb.test()
async def deterministic_mixed_traffic_scoreboard(dut):
    """Check a deterministic mix of writes/reads against a Python reference model."""
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)

    reference = {}
    vectors = [
        (True, 0x03, 0xA1), (True, 0x43, 0xB2), (True, 0x83, 0xC3),
        (True, 0xC3, 0xD4), (True, 0x23, 0xE5), (True, 0x63, 0xF6),
        (False, 0x03, 0), (False, 0x43, 0), (False, 0x83, 0),
        (False, 0xC3, 0), (False, 0x23, 0), (False, 0x63, 0),
        (True, 0x03, 0x5A), (False, 0x03, 0),
    ]
    for write, addr, data in vectors:
        if write:
            await transact(dut, True, addr, data)
            reference[addr] = data
        else:
            result = await transact(dut, False, addr)
            expected = reference.get(addr, 0)
            assert result == expected, (
                f"Scoreboard mismatch at 0x{addr:02X}: "
                f"expected 0x{expected:02X}, got {result!r}"
            )

@cocotb.test()
async def reset_clears_controller_and_memory(dut):
    """Reset during activity returns the controller to a clean initial state."""
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)
    await transact(dut, True, 0xA5, 0xE7)

    # Start refresh, then assert asynchronous active-low reset while busy.
    dut.refresh_req.value = 1
    await cycle(dut)
    dut.refresh_req.value = 0
    dut.rst_n.value = 0
    await Timer(1, unit="ns")
    assert int(dut.req_ready.value) == 1, "Controller should return to IDLE on reset"
    assert int(dut.rsp_valid.value) == 0, "Reset must clear response-valid"
    assert int(dut.refresh_done.value) == 0, "Reset must clear refresh-done"
    dut.rst_n.value = 1
    await cycle(dut)

    result = await transact(dut, False, 0xA5)
    assert result == 0, f"Reset should clear behavioral memory; got 0x{result:02X}"


@cocotb.test()
async def address_space_sweep(dut):
    """Exercise every 8-bit address and verify all 256 stored bytes."""
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)

    expected = {}
    banks = set()
    rows = set()
    columns = set()
    for addr in range(256):
        data = (addr * 73 + 19) & 0xFF
        await transact(dut, True, addr, data)
        expected[addr] = data
        banks.add((addr >> 6) & 0x3)
        rows.add((addr >> 4) & 0x3)
        columns.add(addr & 0xF)

    for addr in range(256):
        result = await transact(dut, False, addr)
        assert result == expected[addr], (
            f"Address sweep mismatch at 0x{addr:02X}: "
            f"expected 0x{expected[addr]:02X}, got {result!r}"
        )

    assert banks == {0, 1, 2, 3}, f"Not all banks covered: {banks}"
    assert rows == {0, 1, 2, 3}, f"Not all rows covered: {rows}"
    assert columns == set(range(16)), f"Not all columns covered: {columns}"
    dut._log.info(
        "Address-space coverage: addresses=256/256, banks=4/4, rows=4/4, columns=16/16"
    )


@cocotb.test()
async def consecutive_transactions_keep_data_isolated(dut):
    """Consecutive transactions to different addresses do not cross-contaminate data."""
    cocotb.start_soon(pulse_clock(dut))
    await reset_dut(dut)

    vectors = [
        (0x00, 0x00), (0xFF, 0xFF), (0x7F, 0x80),
        (0x80, 0x7F), (0x55, 0xAA), (0xAA, 0x55),
    ]
    for addr, data in vectors:
        await transact(dut, True, addr, data)
    for addr, data in reversed(vectors):
        result = await transact(dut, False, addr)
        assert result == data, (
            f"Address 0x{addr:02X}: expected 0x{data:02X}, got {result!r}"
        )

