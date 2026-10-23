TOPLEVEL_LANG = verilog
SIM ?= verilator

VERILOG_SOURCES = $(PWD)/rtl/ddr_controller.sv
TOPLEVEL = ddr_controller
MODULE = test_ddr_controller

export PYTHONPATH := $(PWD)/tests:$(PYTHONPATH)

COMPILE_ARGS += --timing
COMPILE_ARGS += -Wno-fatal

include $(shell cocotb-config --makefiles)/Makefile.sim
