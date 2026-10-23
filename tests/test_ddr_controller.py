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
