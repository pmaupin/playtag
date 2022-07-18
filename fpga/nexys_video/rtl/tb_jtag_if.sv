`default_nettype none
/*

This module supports using a JTAG user instruction to move arbitrary streams of data.

It imposes very few constraints on its client:

  - The first bit received must be a zero.  (LSB of command)
  - Each transaction must be an integer number of bytes long
  - Each command must be at least 2 bytes long
  - Data sent back may start on the second byte.  It could
    overlap the next_command if required.
  - The client's clock should run continuously and should be
    "fast enough" compared to JTAG clock.
        "Fast enough" depends on the state machine of the client,
        any pipelining to RAMs, etc.  The current tb_ctl client
        requires a system clock that is 2x the maximum JTAG
        clock rate.

*/

module tb_jtag_if(
    // Control
    input  wire          sysclk,
    input  wire          sys_rstn,
    input  wire          rsp_data_rdy,   // Set when to_jtag updated
    input  wire          cmd_finishing,  // Should be set true for one sysclk after receiving
                                         // second-to-last command byte.
    output logic         start_cmd,      // Set true for one sysclk cycle when start bit received
    output logic         cmd_data_rdy,   // Set true for one sysclk cycle after every data byte received
                                         // If cmd_data_rdy and start_cmd are set on same cycle, cmd_data_rdy
                                         // indicates availability of last byte of previous command, and
                                         // start_cmd indicates that a new command is starting.
    output wire          jtag_inactive,  // Remains true while JTAG is inactive (JTAG user register not selected).
                                         // This may happen at any time, e.g. in the middle of a command, which
                                         // should then be considered aborted/abandoned.
    // Data
    // NOTE:  Data follows JTAG/UART convention of LSB first, not MSB first, on the wire.
    //        This is opposite from the SPI convention.

    input  wire  [7:0]   to_jtag,         // Should only be changed one clock after start_cmd or cmd_data_rdy.
    output logic [7:0]   from_jtag        // Should be sampled one clock after cmd_data_rdy.
);

parameter integer JTAG_CHAIN = 4;

logic [7:0] jtag_tdo_vec,    next_jtag_tdo_vec;
wire  [2:0] jtag_gray;
wire  [7:0] jtag_tdi_vec;

tb_jtag_cross  #(.JTAG_CHAIN(JTAG_CHAIN)) jtag_x(
    .sysclk(sysclk),
    .sys_rstn(sys_rstn),
    .jtag_tdo_vec(jtag_tdo_vec),
    .jtag_inactive(jtag_inactive),
    .jtag_gray(jtag_gray),
    .jtag_tdi_vec(jtag_tdi_vec)
);

wire [2:0] base_counter = {jtag_gray[2], jtag_gray[2] ^ jtag_gray[1],
                           jtag_gray[2] ^ jtag_gray[1] ^ jtag_gray[0]};

logic                      next_start_cmd;
logic                      next_cmd_data_rdy;
logic [7:0]                next_from_jtag;
logic       cmd_ended,     next_cmd_ended;
logic [2:0] rd_ptr,        next_rd_ptr;
logic       hunting,       next_hunting;
logic [2:0] tdi_counter,   next_tdi_counter;
logic [6:0] tdi_shift,     next_tdi_shift;
logic [2:0] wr_ptr,        next_wr_ptr;
logic [2:0] tdo_counter,   next_tdo_counter;
logic [6:0] tdo_shift,     next_tdo_shift;
logic       tdo_avail,     next_tdo_avail;


always_comb begin
    next_start_cmd     = 1'b0;
    next_cmd_data_rdy  = 1'b0;
    next_from_jtag     = from_jtag;
    next_cmd_ended     = cmd_ended || cmd_finishing;
    next_rd_ptr        = rd_ptr;
    next_hunting       = hunting;
    next_tdi_counter   = tdi_counter;
    next_tdi_shift     = tdi_shift;
    next_wr_ptr        = wr_ptr;
    next_tdo_counter   = tdo_counter;
    next_tdo_shift     = tdo_shift;
    next_tdo_avail     = tdo_avail || rsp_data_rdy;
    next_jtag_tdo_vec  = jtag_tdo_vec;

    if (jtag_inactive) begin
        next_hunting = 1'b1;
        next_rd_ptr  = base_counter;
        next_cmd_ended = 1'b0;
        next_tdo_counter = 3'b0;
    end else if (base_counter!= rd_ptr) begin
        next_rd_ptr = rd_ptr + 1;
        next_tdi_shift = {jtag_tdi_vec[next_rd_ptr], tdi_shift[6:1]};
        next_tdi_counter = tdi_counter + 1;
        if (hunting) begin
            if (!jtag_tdi_vec[next_rd_ptr]) begin
                next_hunting = 1'b0;
                next_tdi_counter=1;
                next_start_cmd = 1'b1;
                next_wr_ptr = rd_ptr - 1;
                next_tdo_counter = 3'b0;
            end
        end else if (tdi_counter == 7) begin
            next_from_jtag = {jtag_tdi_vec[next_rd_ptr], tdi_shift[6:0]};
            next_cmd_data_rdy = !hunting;
            next_hunting = cmd_ended || cmd_finishing || hunting;
            next_cmd_ended  = 1'b0;
        end
    end

    if (jtag_inactive) begin
        next_tdo_counter = 3'b0;
        next_tdo_avail = 1'b0;
    end else if (wr_ptr != base_counter) begin
        if (tdo_counter) begin
            {next_tdo_shift, next_jtag_tdo_vec[wr_ptr]} = tdo_shift;
            next_tdo_counter = tdo_counter + 1;
            next_wr_ptr = wr_ptr + 1;
        end else if (next_tdo_avail) begin
            {next_tdo_shift, next_jtag_tdo_vec[wr_ptr]} = to_jtag;
            next_tdo_counter = 1;
            next_wr_ptr = wr_ptr + 1;
            next_tdo_avail = 1'b0;
        end
    end
end

always @(posedge sysclk or negedge sys_rstn)
    if (!sys_rstn) begin
        jtag_tdo_vec  <= 8'b0;
        start_cmd     <= 1'b0;
        cmd_data_rdy  <= 1'b0;
        from_jtag     <= 8'b0;
        cmd_ended     <= 1'b0;
        rd_ptr        <= 3'b0;
        hunting       <= 1'b0;
        tdi_counter   <= 3'b0;
        tdi_shift     <= 7'b0;
        wr_ptr        <= 3'b0;
        tdo_counter   <= 3'b0;
        tdo_shift     <= 7'b0;
        tdo_avail     <= 1'b0;
    end else begin
        jtag_tdo_vec  <= next_jtag_tdo_vec;
        start_cmd     <= next_start_cmd;
        cmd_data_rdy  <= next_cmd_data_rdy;
        from_jtag     <= next_from_jtag;
        cmd_ended     <= next_cmd_ended;
        rd_ptr        <= next_rd_ptr;
        hunting       <= next_hunting;
        tdi_counter   <= next_tdi_counter;
        tdi_shift     <= next_tdi_shift;
        wr_ptr        <= next_wr_ptr;
        tdo_counter   <= next_tdo_counter;
        tdo_shift     <= next_tdo_shift;
        tdo_avail     <= next_tdo_avail;
    end

endmodule

