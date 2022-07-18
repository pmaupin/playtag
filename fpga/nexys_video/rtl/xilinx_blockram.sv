/*

    xilinx_dp_ram.sv

    A part of playtag.
    Copyright (C) 2011, 2022 by Patrick Maupin.  All rights reserved.
    License information at: https://github.com/pmaupin/playtag/blob/master/LICENSE.txt

    This module allows direct verilog instantiation of a Xilinx dual-port
    blockram, in NO-CHANGE mode.

    NO-CHANGE means that on data write, the read data
    for that port does not change.

    Do not change the code in this module without good reason;
    Xilinx tools that decide something works as a RAM
    are somewhat finicky.

    Also, DO NOT directly drive the write disable if unnecessary;
    that will make it difficult to drive from higher in the hierarchy.

    All enables are active high.
*/

module xilinx_blockram
  #(
    parameter ADDR_WIDTH=13,    // width of address bus
    parameter DATA_WIDTH=32,    // width of data bus, e.g. 32
    parameter WRITE_WIDTH=8,    // width of each write, e.g. 8
    parameter HEX_FILE="",
    parameter BIN_FILE="",
    parameter DUAL_PORT=0
    ) (
       input wire clkA,
       input wire enaA,
       input wire [DATA_WIDTH / WRITE_WIDTH-1:0] weA = 'b0,
       input wire write_disableA = 1'b0,
       input wire [ADDR_WIDTH-1:0] addrA,
       input wire [DATA_WIDTH-1:0] dinA = 'b0,
       output reg [DATA_WIDTH-1:0] doutA,

       // Use of second port is completely optional.  It may
       // even be used from way above in the hierarchy, IF
       // there is no array of module instances anywhere in
       // the hierarchy.  (E.g. to allow backdoor update of ROM contents.)

       input wire clkB='b0,
       input wire enaB='b0,
       input wire write_disableB = 1'b0,
       input wire [DATA_WIDTH / WRITE_WIDTH-1:0] weB='b0,
       input wire [ADDR_WIDTH-1:0] addrB='b0,
       input wire [DATA_WIDTH-1:0] dinB='b0,
       output reg [DATA_WIDTH-1:0] doutB
    );

   (* ram_style = "block" *)       reg [DATA_WIDTH-1:0] ram [2**ADDR_WIDTH-1:0];

   // Port A writes
   genvar i;
   generate
      for(i=0;i<DATA_WIDTH / WRITE_WIDTH;i=i+1) begin
         always @ (posedge clkA) begin
            if(enaA) begin
               if(weA[i] && !write_disableA) begin
                  ram[addrA][i*WRITE_WIDTH +: WRITE_WIDTH] <= dinA[i*WRITE_WIDTH +: WRITE_WIDTH];
               end
            end
         end
      end
   endgenerate

   // Port A reads
   always @ (posedge clkA) begin
      if(enaA) begin
         if (~|weA)
           doutA <= ram[addrA];
      end
   end

if (DUAL_PORT) begin
   // Port B writes
      for(i=0;i<DATA_WIDTH / WRITE_WIDTH;i=i+1) begin
         always @ (posedge clkB) begin
            if(enaB) begin
               if(weB[i] && !write_disableB) begin
                  ram[addrB][i*WRITE_WIDTH +: WRITE_WIDTH] <= dinB[i*WRITE_WIDTH +: WRITE_WIDTH];
               end
            end
         end
      end

   // Port B reads
   always @ (posedge clkB) begin
      if(enaB) begin
         if (~|weB)
           doutB <= ram[addrB];
      end
   end
end

   initial
      if (HEX_FILE != "")
         $readmemh(HEX_FILE, ram);
      else if (BIN_FILE != "")
         $readmemb(BIN_FILE, ram);

endmodule
