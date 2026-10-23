`timescale 1ns/1ps

// Educational DDR-inspired controller.
// This module is NOT a JEDEC-compliant DDR controller.
module ddr_controller #(
    parameter int unsigned T_RCD = 2,
    parameter int unsigned T_RP  = 2,
    parameter int unsigned T_RFC = 4
) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       req_valid,
    output logic       req_ready,
    input  logic       req_write,
    input  logic [7:0] req_addr,
    input  logic [7:0] req_wdata,
    output logic       rsp_valid,
    output logic [7:0] rsp_rdata,
    input  logic       refresh_req,
    output logic       refresh_done
);

    localparam int unsigned MAX_DELAY =
        (T_RCD > T_RP) ? ((T_RCD > T_RFC) ? T_RCD : T_RFC)
                       : ((T_RP > T_RFC) ? T_RP : T_RFC);
    localparam int unsigned TIMER_W = (MAX_DELAY < 2) ? 1 : $clog2(MAX_DELAY + 1);

    typedef enum logic [3:0] {
        ST_IDLE, ST_PRECHARGE, ST_ACTIVATE, ST_RCD_WAIT,
        ST_ACCESS, ST_RESPONSE, ST_REFRESH_PRE, ST_REFRESH_WAIT
    } state_t;

    state_t state;
    logic [3:0] bank_open;
    logic [1:0] open_row [0:3];
    logic [TIMER_W-1:0] timer;
    logic [7:0] memory [0:255];

    logic [1:0] saved_bank;
    logic [1:0] saved_row;
    logic [7:0] saved_addr;
    logic       saved_write;
    logic [7:0] saved_wdata;
    integer i;

    always_comb begin
        req_ready = (state == ST_IDLE) && !refresh_req;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= ST_IDLE;
            bank_open    <= 4'b0000;
            timer        <= '0;
            rsp_valid    <= 1'b0;
            rsp_rdata    <= '0;
            refresh_done <= 1'b0;
            saved_bank   <= '0;
            saved_row    <= '0;
            saved_addr   <= '0;
            saved_write  <= 1'b0;
            saved_wdata  <= '0;
            for (i = 0; i < 4; i = i + 1)
                open_row[i] <= '0;
            for (i = 0; i < 256; i = i + 1)
                memory[i] <= '0;
        end else begin
            rsp_valid    <= 1'b0;
            refresh_done <= 1'b0;

            case (state)
                ST_IDLE: begin
                    if (refresh_req) begin
                        if (|bank_open) begin
                            state <= ST_REFRESH_PRE;
                            timer <= T_RP;
                        end else begin
                            timer <= T_RFC;
                            state <= (T_RFC == 0) ? ST_IDLE : ST_REFRESH_WAIT;
                            if (T_RFC == 0)
                                refresh_done <= 1'b1;
                        end
                    end else if (req_valid && req_ready) begin
                        saved_addr  <= req_addr;
                        saved_bank  <= req_addr[7:6];
                        saved_row   <= req_addr[5:4];
                        saved_write <= req_write;
                        saved_wdata <= req_wdata;

                        if (bank_open[req_addr[7:6]] &&
                            (open_row[req_addr[7:6]] != req_addr[5:4])) begin
                            timer <= T_RP;
                            state <= (T_RP == 0) ? ST_ACTIVATE : ST_PRECHARGE;
                        end else if (!bank_open[req_addr[7:6]]) begin
                            state <= ST_ACTIVATE;
                        end else begin
                            // Row hit: this teaching model skips ACTIVATE/RCD.
                            state <= ST_ACCESS;
                        end
                    end
                end

                ST_PRECHARGE: begin
                    if (timer > 1) timer <= timer - 1'b1;
                    else begin
                        bank_open[saved_bank] <= 1'b0;
                        state <= ST_ACTIVATE;
                    end
                end

                ST_ACTIVATE: begin
                    bank_open[saved_bank] <= 1'b1;
                    open_row[saved_bank] <= saved_row;
                    timer <= T_RCD;
                    state <= (T_RCD == 0) ? ST_ACCESS : ST_RCD_WAIT;
                end

                ST_RCD_WAIT: begin
                    if (timer > 1) timer <= timer - 1'b1;
                    else state <= ST_ACCESS;
                end

                ST_ACCESS: begin
                    if (saved_write)
                        memory[saved_addr] <= saved_wdata;
                    else
                        rsp_rdata <= memory[saved_addr];
                    state <= ST_RESPONSE;
                end

                ST_RESPONSE: begin
                    rsp_valid <= !saved_write;
                    state <= ST_IDLE;
                end

                ST_REFRESH_PRE: begin
                    if (timer > 1) timer <= timer - 1'b1;
                    else begin
                        bank_open <= 4'b0000;
                        timer <= T_RFC;
                        state <= (T_RFC == 0) ? ST_IDLE : ST_REFRESH_WAIT;
                        if (T_RFC == 0)
                            refresh_done <= 1'b1;
                    end
                end

                ST_REFRESH_WAIT: begin
                    if (timer > 1) timer <= timer - 1'b1;
                    else begin
                        refresh_done <= 1'b1;
                        state <= ST_IDLE;
                    end
                end

                default: begin
                    state <= ST_IDLE;
                    bank_open <= 4'b0000;
                    timer <= '0;
                end
            endcase
        end
    end
endmodule
