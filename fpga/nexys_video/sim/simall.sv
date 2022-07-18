/*

This simulation testbench is just smart enough to run a few transactions.  Most of the testing
is done from Python on real JTAG.

There are two modules here.  The top one simply instantiates the next level, and then
mirrors a bunch of wires from down in the design, to make it easy to view what is going on
in simulation.

The bottom one actually runs the transactions.
*/
module simall;

simit sim();

wire       jtag_clk        = sim.dut.ctl.jtag_if.jtag_x.gated_tck;
wire       jtag_rstn       = sim.dut.ctl.jtag_if.jtag_x.jtag_rstn;
wire       jtag_sel        = sim.dut.ctl.jtag_if.jtag_x.jtag_sel;
wire       jtag_tdi        = sim.dut.ctl.jtag_if.jtag_x.tdi;
wire       jtag_tdo        = sim.dut.ctl.jtag_if.jtag_x.tdo;
wire [7:0] x_tdo_vec       = sim.dut.ctl.jtag_if.jtag_x.tdo_vec_x1;
wire [7:0] x_tdi_vec       = sim.dut.ctl.jtag_if.jtag_x.tdi_vec;
wire       x_tdi_dly       = sim.dut.ctl.jtag_if.jtag_x.tdi_dly;
wire [2:0] x_gray          = sim.dut.ctl.jtag_if.jtag_x.gray;
wire [2:0] x_bitctr        = sim.dut.ctl.jtag_if.jtag_x.bitctr;
wire       spacer1         = 1'bz;
wire       x_sysclk        = sim.dut.ctl.jtag_if.jtag_x.sysclk;
wire [7:0] x_tdo_byte      = sim.dut.ctl.jtag_if.jtag_x.tdo_vec_x2;
wire [7:0] x_tdi_byte      = sim.dut.ctl.jtag_if.jtag_x.tdi_vec_x2;
wire [2:0] x_gray_cross1   = sim.dut.ctl.jtag_if.jtag_x.gray_x1;
wire [2:0] x_gray_cross2   = sim.dut.ctl.jtag_if.jtag_x.gray_x2;
wire [1:0] x_jtag_in_reset = sim.dut.ctl.jtag_if.jtag_x.trst;
wire       spacer2         = 1'bz;

wire       i_sysclk         = sim.dut.ctl.jtag_if.jtag_x.sysclk;
wire       i_hunting        = sim.dut.ctl.jtag_if.hunting;
wire       i_start_cmd      = sim.dut.ctl.jtag_if.start_cmd;
wire       i_cmd_data_rdy   = sim.dut.ctl.jtag_if.cmd_data_rdy;
wire       i_jtag_inactive  = sim.dut.ctl.jtag_if.jtag_inactive;
wire       spacer2a         = 1'bz;
wire       i_sysclk2        = sim.dut.ctl.jtag_if.jtag_x.sysclk;
wire [2:0] i_base_counter   = sim.dut.ctl.jtag_if.base_counter;
wire [2:0] i_rd_ptr         = sim.dut.ctl.jtag_if.rd_ptr;
wire [7:0] i_jtag_tdi_vec   = sim.dut.ctl.jtag_if.jtag_tdi_vec;
wire [2:0] i_tdi_counter    = sim.dut.ctl.jtag_if.tdi_counter;
wire [6:0] i_tdi_shift      = sim.dut.ctl.jtag_if.tdi_shift;
wire [7:0] i_from_jtag      = sim.dut.ctl.jtag_if.from_jtag;
wire       spacer2b         = 1'bz;
wire [7:0] i_jtag_tdo_vec   = sim.dut.ctl.jtag_if.jtag_tdo_vec;
wire       i_cmd_ended      = sim.dut.ctl.jtag_if.cmd_ended;
wire [2:0] i_wr_ptr         = sim.dut.ctl.jtag_if.wr_ptr;
wire [2:0] i_tdo_counter    = sim.dut.ctl.jtag_if.tdo_counter;
wire [6:0] i_tdo_shift      = sim.dut.ctl.jtag_if.tdo_shift;
wire       spacer3          = 1'bz;

wire             sysclk         = sim.dut.ctl.sysclk;
wire [7:0]         ce           = sim.dut.ctl.ce;
wire               we           = sim.dut.ctl.we;
wire [31:2]        addr         = sim.dut.ctl.addr;
wire [31:0]        wd           = sim.dut.ctl.wd;
wire [3:0]         bytesel      = sim.dut.ctl.bytesel;
wire [2:0]         invalid_state= sim.dut.ctl.invalid_state;
wire [7:0]         cmd_byte     = sim.dut.ctl.cmd_byte;
wire               launch_write = sim.dut.ctl.launch_write;
wire               launch_read  = sim.dut.ctl.launch_read;
wire               launched     = sim.dut.ctl.launched;
wire [31:2]        pre_addr     = sim.dut.ctl.pre_addr;
wire [31:0]        pre_wd       = sim.dut.ctl.pre_wd;
wire [3:0]         pre_bytesel  = sim.dut.ctl.pre_bytesel;

wire [sim.dut.ctl.BAD_2:sim.dut.ctl.IDLE]
                   cmd_state    = sim.dut.ctl.cmd_state;
wire [5:0]         sub_state    = sim.dut.ctl.sub_state;
wire               rsp_data_rdy = sim.dut.ctl.rsp_data_rdy;
wire               cmd_finishing= sim.dut.ctl.cmd_finishing;
wire [1:0]         start_byte   = sim.dut.ctl.start_byte;
wire [7:0]         rd_mux       = sim.dut.ctl.rd_mux;
wire               arm_count    = sim.dut.ctl.arm_count;
wire [7:0]         byte_counter = sim.dut.ctl.byte_counter;
wire [2:0]         count_done   = sim.dut.ctl.count_done;
wire [7:0]         to_jtag      = sim.dut.ctl.to_jtag;
wire [8*32-1:0]    rd_delay     = sim.dut.ctl.rd_delay;
wire [31:0]        rd_mux1      = sim.dut.ctl.rd_mux1;

wire               spacer4          = 1'bz;
wire               ram_clk      = sim.dut.RAM.clkA;
wire               ram_ce       = sim.dut.RAM.enaA;
wire [3:0]         ram_bytesel  = sim.dut.RAM.weA;
wire [12:0]        ram_addr     = sim.dut.RAM.addrA;
wire [31:0]        ram_wd       = sim.dut.RAM.dinA;
wire [31:0]        ram_rd       = sim.dut.RAM.doutA;
wire [7:0]         led_values   = sim.dut.led_values;

wire               spacer5          = 1'bz;
wire       a_sysclk         = sim.dut.ctl.jtag_if.jtag_x.sysclk;
wire       a_jtag_inactive  = sim.dut.ctl.jtag_if.jtag_inactive;
wire       a_hunting        = sim.dut.ctl.jtag_if.hunting;
wire       a_start_cmd      = sim.dut.ctl.jtag_if.start_cmd;
wire       a_cmd_data_rdy   = sim.dut.ctl.jtag_if.cmd_data_rdy;
wire [7:0] a_from_jtag      = sim.dut.ctl.jtag_if.from_jtag;
wire       a_cmd_ended      = sim.dut.ctl.jtag_if.cmd_ended;
wire [sim.dut.ctl.BAD_2:sim.dut.ctl.IDLE]
                   a_cmd_state    = sim.dut.ctl.cmd_state;
wire [5:0]         a_sub_state    = sim.dut.ctl.sub_state;
wire               a_rsp_data_rdy = sim.dut.ctl.rsp_data_rdy;
wire               a_cmd_finishing= sim.dut.ctl.cmd_finishing;
wire [1:0]         a_start_byte   = sim.dut.ctl.start_byte;
wire [7:0]         a_rd_mux       = sim.dut.ctl.rd_mux;
wire               a_arm_count    = sim.dut.ctl.arm_count;
wire [7:0]         a_byte_counter = sim.dut.ctl.byte_counter;
wire [2:0]         a_count_done   = sim.dut.ctl.count_done;
wire [7:0]         a_led_values   = sim.dut.led_values;

endmodule;


module simit;

logic clk = 0;
logic sys_rstn = 0;
logic porn = 0;

wire tdo;
logic tck = 0;
logic tdi = 0;
logic tms = 0;

tb_top dut(.clk(clk), .cpu_resetn(sys_rstn));

JTAG_SIME2 #(.PART_NAME("7a200t")) jtag_it(.TDO(tdo), .TCK(tck), .TDI(tdi), .TMS(tms));

initial forever begin
    #10;
    clk = !clk;
end

logic [127:0] tdo_vec;

task do_jtag(input logic [7:0] num_bits,
             input logic [127:0] tdivec = 'b0,
             input logic [127:0] tmsvec = 'b0);
    integer i;
    begin
        tdo_vec = 'b0;
        for (i=0; i < num_bits; i+=1) begin
            tms = tmsvec[i];
            tdi = tdivec[i];
            tck = 0;
            #100;
            tck = 1;
            #100;
            tdo_vec[i] = tdo;
        end
        $display("%s TDO = %0h", jtag_it.jtag_state_name, tdo_vec);
    end
endtask

initial begin
    #100;
    porn = 1;
    #100;
    sys_rstn = 1;
    // Push USER4 into IR, then switch to DR_SHIFT
    do_jtag(20, 'b11111000111111111111, 'b00111000000011011111);

    do_jtag(10, 'b1111111111);

    // Write to the memory

    do_jtag(8,  'b0001_1110);
    do_jtag(32, 'h00000000);
    do_jtag(8,  'h4);
    do_jtag(40, 'hFF98765432);

    // Read from the memory

    do_jtag(8,  'b0000_1110);
    do_jtag(32, 'h00000000);
    do_jtag(8,  'h4);
    do_jtag(40, 'hFFFFFFFFFF);

    // Two reads with space between them
    do_jtag(8,  'b0);
    do_jtag(32, 'h12345678);
    do_jtag(8,  'h4);
    do_jtag(40, 'hFFFFFFFFFF);

    do_jtag(8,  'b10);
    do_jtag(32, 'b0);
    do_jtag(8,  'h4);
    do_jtag(64, 'hFFFFFFFFFFFFFFFF);

    // Same two reads back to back
    do_jtag(8,  'b0);
    do_jtag(32, 'h12345678);
    do_jtag(8,  'h4);
    do_jtag(32, 'h00000000);

    do_jtag(8,  'b10);
    do_jtag(32, 'b0);
    do_jtag(8,  'h4);
    do_jtag(64, 'hFFFFFFFFFFFFFFFF);

    // Read from the memory

    do_jtag(8,  'b0000_1110);
    do_jtag(32, 'h00000000);
    do_jtag(8,  'h4);
    do_jtag(40, 'hFFFFFFFFFF);


    // Write to LEDs

    do_jtag(8,  'b0001_0110);
    do_jtag(32, 'h00000000);
    do_jtag(8,  'h1);
    do_jtag(16, 'hFFFF);

    do_jtag(8,  'b0001_0110);
    do_jtag(32, 'h00000000);
    do_jtag(8,  'h1);
    do_jtag(8, 'h00);

    do_jtag(8,  'b0001_0110);
    do_jtag(32, 'h00000000);
    do_jtag(8,  'h1);
    do_jtag(8, 'hF0);

    do_jtag(2, 'hFF);

    $finish();
end

endmodule
