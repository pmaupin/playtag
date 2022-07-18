`default_nettype none
/*
    A part of playtag.
    Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
    License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt


This module clock-crosses a JTAG interface to an internal system clock.

Goals of this module include:
  - Encapsulate vendor-specific low level JTAG module (currently Xilinx BSCANE2)
  - Reduce logic and number of loads on JTAG clock
  - Reduce logic (and required setup time) on TDO and TDI pins
  - Contain all clock-crossing flops
  - Present an 8 bit FIFO interface both directions to reduce the required
    system clock frequency.

This module is dumb.  It is up to higher level modules to figure
out where we are in the bit stream, and pull TDI bits out of the FIFO and
push TDO bits into the FIFO, for example.

The gray counter and the jtag_inactive output are double-clocked on the
sysclk domain on flops placed as physically close to each other as possible.

The data signals are clocked on both domains on flops that are placed
as physically close to each other as possible.
*/

module tb_jtag_cross(
    // Control
    input  wire         sysclk,
    input  wire         sys_rstn,

    input  wire [7:0]   jtag_tdo_vec,  // Vector of bits (FIFO)

    output wire         jtag_inactive, // In reset, or our register not selected
    output wire [2:0]   jtag_gray,     // Gray code counter for FIFOs
    output wire [7:0]   jtag_tdi_vec   // Vector of bits (FIFO)
);


parameter integer JTAG_CHAIN = 4;

wire  gated_tck;
wire  trst;
wire  jtag_sel;
wire  tdi;
wire  jtag_rstn;

(* ASYNC_REG = "TRUE" *)  logic [7:0] tdo_vec_x1;
(* ASYNC_REG = "TRUE" *)  logic [7:0] tdo_vec_x2;
(* ASYNC_REG = "TRUE" *)  logic tdo;
(* ASYNC_REG = "TRUE" *)  logic [7:0] tdi_vec;
                          logic       tdi_dly;
                          logic [2:0] gray;
                          logic [2:0] bitctr;

(* ASYNC_REG = "TRUE" *)  logic [7:0] tdi_vec_x2;
(* ASYNC_REG = "TRUE" *)  logic [2:0] gray_x1;
(* ASYNC_REG = "TRUE" *)  logic [2:0] gray_x2;
(* ASYNC_REG = "TRUE" *)  logic [2:0] inactive_x;

BSCANE2 #(.JTAG_CHAIN(JTAG_CHAIN)) sys_jtag(
  .CAPTURE(),
  .DRCK(gated_tck),
  .RESET(trst),
  .RUNTEST(),
  .SEL(jtag_sel),
  .SHIFT(),
  .TCK(),
  .TDI(tdi),
  .TMS(),
  .UPDATE(),
  .TDO(tdo)
);

assign jtag_rstn = !trst && jtag_sel;

always @(posedge gated_tck or negedge jtag_rstn)
    if (!jtag_rstn) begin
        tdo             <= 1'b1;
        tdo_vec_x2      <= 8'b11111111;
        tdi_vec         <= 8'b11111111;
        tdi_dly         <= 1'b1;
        gray            <= 3'b0;
        bitctr          <= 3'b0;
    end else begin
        tdo             <= tdo_vec_x2[bitctr];
        tdo_vec_x2      <= tdo_vec_x1;
        tdi_vec[bitctr] <= tdi_dly;
        tdi_dly         <= tdi;
        gray            <= {bitctr[2], bitctr[2:1] ^ bitctr[1:0]};
        bitctr          <= bitctr + 1;
    end

always @(posedge sysclk or negedge sys_rstn)
    if (!sys_rstn) begin
        tdo_vec_x1 <= 8'b11111111;
        tdi_vec_x2 <= 8'b11111111;
        gray_x1    <= 3'b0;
        gray_x2    <= 3'b0;
        inactive_x <= 3'b111;
    end else begin
        tdo_vec_x1 <= jtag_tdo_vec;
        tdi_vec_x2 <= tdi_vec;
        gray_x1    <= gray;
        gray_x2    <= gray_x1;
        inactive_x <= {inactive_x, !jtag_rstn};
    end

assign jtag_inactive = inactive_x[2];
assign jtag_gray     = gray_x2;
assign jtag_tdi_vec  = tdi_vec_x2;

endmodule
