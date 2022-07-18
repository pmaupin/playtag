`default_nettype none
/*
    Sits on top of a byte-wide interface to JTAG and
    introduces control semantics, with 32 bit addressing,
    32 bit memories, etc.

    Command structure:
      - Command byte
      - Addr 0 (LSB)
      - Addr 1
      - Addr 2
      - Addr 3 (MSB)
      - Count (0 means 256 bytes)
      - data -- 1 to 256 bytes

   The command byte is organized as follows by bit:
       7-4: Command type
       3-1: Mem space selector
       0: 0 (start bit of command)

   Valid commands (command type selector, bits 7:4):
       0 - read
       1 - write
       2-15 - reserved

   Up to 8 external memories can be addressed.

   Asynchronous status may be returned on each command.

*/

module tb_ctl (
    input wire          sysclk,
    input wire          sys_rstn,
    input wire  [31:0]  rd0 = 'b0,
    input wire  [31:0]  rd1 = 'b0,
    input wire  [31:0]  rd2 = 'b0,
    input wire  [31:0]  rd3 = 'b0,
    input wire  [31:0]  rd4 = 'b0,
    input wire  [31:0]  rd5 = 'b0,
    input wire  [31:0]  rd6 = 'b0,
    input wire  [31:0]  rd7 = 'b0,
    input wire  [31:0]  async_status = 'b0,

    output logic [7:0]  ce,
    output logic        we,

    output logic [31:2] addr,
    output logic [31:0] wd,
    output logic [3:0]  bytesel
);

parameter integer JTAG_CHAIN = 4;

typedef enum {IDLE, WAIT_CMD, WAIT_ADDR0,  WAIT_ADDR1,  WAIT_ADDR2, WAIT_ADDR3,
                    WAIT_LEN, WAIT_RDATA, WAIT_WDATA, BAD_1, BAD_2} state_type;

wire                start_cmd;
wire                cmd_data_rdy;
wire                jtag_inactive;
wire  [7:0]         from_jtag;

logic [2:0]         invalid_state,  next_invalid_state;
logic [7:0]         cmd_byte,       next_cmd_byte;
logic               launch_write,   next_launch_write;
logic               launch_read,    next_launch_read;
logic               launched,       next_launched;

logic                               next_we;
logic [7:0]                         next_ce;

logic [31:2]        pre_addr,       next_pre_addr;
logic [31:0]        pre_wd,         next_pre_wd;
logic [3:0]         pre_bytesel,    next_pre_bytesel;
logic [BAD_2:IDLE]  cmd_state,      next_cmd_state;
logic [5:0]         sub_state,      next_sub_state;
logic               rsp_data_rdy,   next_rsp_data_rdy;
logic               cmd_finishing,  next_cmd_finishing;
logic [1:0]         start_byte,     next_start_byte;
logic [7:0]         rd_mux,         next_rd_mux;
logic               arm_count,      next_arm_count;
logic [7:0]         byte_counter,   next_byte_counter;
logic [2:0]         count_done,     next_count_done;

logic [7:0]         to_jtag;
logic [8*32-1:0]    rd_delay;
logic [31:0]        rd_mux1;
logic [7:0]         rd_mux_aux,     next_rd_mux_aux;

tb_jtag_if #(.JTAG_CHAIN(JTAG_CHAIN)) jtag_if(
    .sysclk(sysclk),
    .sys_rstn(sys_rstn),
    .rsp_data_rdy(rsp_data_rdy),
    .cmd_finishing(cmd_finishing),
    .start_cmd(start_cmd),
    .cmd_data_rdy(cmd_data_rdy),
    .jtag_inactive(jtag_inactive),
    .to_jtag(to_jtag),
    .from_jtag(from_jtag)
);

always @(posedge sysclk or negedge sys_rstn)
    if (!sys_rstn) begin
        invalid_state <= 3'b111;
        cmd_byte      <= 8'b0;
        launch_write  <= 1'b0;
        launch_read   <= 1'b0;
        launched      <= 1'b0;
        we            <= 1'b0;
        ce            <= 8'b0;
        pre_addr      <= 30'b0;
        pre_wd        <= 32'b0;
        pre_bytesel   <= 4'b0;
        cmd_state     <=  'b0;
        sub_state     <=  'b0;
        rsp_data_rdy  <= 1'b0;
        cmd_finishing <= 1'b0;
        start_byte    <= 2'b0;
        rd_mux        <= 8'hA5;
        arm_count     <= 1'b0;
        byte_counter  <= 8'b0;
        count_done    <= 3'b0;
        to_jtag       <= 8'hFF;
        rd_delay      <=  'b0;
        rd_mux1       <= 32'b0;
        addr          <= 30'b0;
        wd            <= 32'b0;
        bytesel       <= 4'b0;
        rd_mux_aux    <= 8'b0;
    end else begin
        invalid_state <= next_invalid_state;
        cmd_byte      <= next_cmd_byte;
        launch_write  <= next_launch_write;
        launch_read   <= next_launch_read;
        launched      <= next_launched;
        pre_addr      <= next_pre_addr;
        pre_wd        <= next_pre_wd;
        pre_bytesel   <= next_pre_bytesel;
        we            <= next_we;
        ce            <= next_ce;
        cmd_state     <= next_cmd_state;
        sub_state     <= next_sub_state;
        rsp_data_rdy  <= next_rsp_data_rdy;
        cmd_finishing <= next_cmd_finishing;
        start_byte    <= next_start_byte;
        rd_mux        <= next_rd_mux;
        arm_count     <= next_arm_count;
        byte_counter  <= next_byte_counter;
        count_done    <= next_count_done;
        to_jtag       <= rd_mux;
        rd_delay      <= {rd7, rd6, rd5, rd4, rd3, rd2, rd1, rd0};
        rd_mux1       <= sub_state[3] ? rd_delay >> (32 * cmd_byte[3:1]) : rd_mux1;
        addr          <= pre_addr;
        wd            <= pre_wd;
        bytesel       <= pre_bytesel;
        rd_mux_aux    <= next_rd_mux_aux;
    end

task change_state(state_type from_state, state_type to_state, logic conditional = 1'b1);
    if (conditional) begin
        next_cmd_state[from_state] = 1'b0;
        next_cmd_state[to_state] = !jtag_inactive;
    end
endtask

always_comb begin
    next_invalid_state[2:1] = invalid_state[1:0];
    next_invalid_state[0] = !cmd_state;
    next_cmd_byte       = cmd_byte;
    next_launch_write   = 1'b0;
    next_launch_read    = 1'b0;
    next_launched       = launch_read || launch_write;
    next_we             = launch_write;
    next_ce             = {7'b0, launch_read || launch_write} << cmd_byte[3:1];
    next_pre_addr       = pre_addr + launched;
    next_pre_wd         = pre_wd;
    next_pre_bytesel    = we ? 4'b0 : pre_bytesel;
    next_cmd_state      = jtag_inactive ? 'b0 : cmd_state;
    next_sub_state      = (cmd_data_rdy) ? 'b1 : (sub_state << 1);
    next_rsp_data_rdy   = sub_state[5];
    next_cmd_finishing  = 1'b0;
    next_start_byte     = start_byte;
    next_rd_mux         = sub_state[4] ? rd_mux_aux : rd_mux;
    next_arm_count      = arm_count && !cmd_data_rdy;
    next_byte_counter   = (arm_count ? from_jtag : byte_counter) - cmd_data_rdy;  // Number after this one
    next_count_done[0]  = !byte_counter;
    next_count_done[1]  = count_done[0] && !arm_count;
    next_count_done[2]  = cmd_data_rdy? count_done[1] : count_done[2];
    next_rd_mux_aux     = rd_mux_aux;

    if (invalid_state[2]) begin
        next_cmd_state[IDLE] = 1'b1;
    end

    unique if (cmd_state[IDLE] && start_cmd) begin
        next_rd_mux_aux = 8'h5A;
        change_state(IDLE, WAIT_CMD);

    end else if (cmd_state[WAIT_CMD] && cmd_data_rdy) begin
        next_rd_mux_aux = async_status[7:0];
        next_cmd_byte = from_jtag;
        change_state(WAIT_CMD, WAIT_ADDR0, !from_jtag[7:5] && !from_jtag[0]);
        change_state(WAIT_CMD, BAD_1,       from_jtag[7:5] ||  from_jtag[0]);

    end else if (cmd_state[WAIT_ADDR0] && cmd_data_rdy) begin
        next_rd_mux_aux = async_status[15:8];
        next_pre_addr[7:2] = from_jtag[7:2];
        next_start_byte    = from_jtag[1:0];
        change_state(WAIT_ADDR0, WAIT_ADDR1);

    end else if (cmd_state[WAIT_ADDR1] && cmd_data_rdy) begin
        next_rd_mux_aux = async_status[23:16];
        next_pre_addr[15:8] = from_jtag;
        change_state(WAIT_ADDR1, WAIT_ADDR2);

    end else if (cmd_state[WAIT_ADDR2] && cmd_data_rdy) begin
        next_rd_mux_aux = async_status[31:24];
        next_pre_addr[23:16] = from_jtag;
        change_state(WAIT_ADDR2, WAIT_ADDR3);

    end else if (cmd_state[WAIT_ADDR3] && cmd_data_rdy) begin
        next_rd_mux_aux = 8'h5A;
        next_pre_addr[31:24] = from_jtag;
        next_arm_count = 1'b1;
        next_launch_read = !cmd_byte[4];
        change_state(WAIT_ADDR3, WAIT_RDATA, !cmd_byte[4]);

    end else if (cmd_state[WAIT_ADDR3] && sub_state[4]) begin
        change_state(WAIT_ADDR3, WAIT_LEN, arm_count);

    end else if (cmd_state[WAIT_LEN] && sub_state[4]) begin
        next_cmd_finishing = count_done[1];
        change_state(WAIT_LEN, WAIT_WDATA);

    end else if (cmd_state[WAIT_RDATA] && cmd_data_rdy) begin
        next_launch_read = (start_byte == 0);

    end else if (cmd_state[WAIT_RDATA] && sub_state[4]) begin
        next_start_byte = start_byte + 1;
        next_cmd_finishing = count_done[1];
        change_state(WAIT_RDATA, IDLE, count_done[1]);
        if (!count_done[1]) begin
            next_rd_mux = rd_mux1 >> (8 * start_byte);
        end

    end else if (cmd_state[WAIT_WDATA] && cmd_data_rdy) begin
        next_pre_wd[start_byte * 8 +: 8] = from_jtag;
        next_pre_bytesel[start_byte] = 1;
        next_rd_mux_aux = byte_counter;

    end else if (cmd_state[WAIT_WDATA] && sub_state[4]) begin
        next_launch_write = (start_byte == 3) || count_done[2];
        next_start_byte = start_byte + 1;
        next_cmd_finishing = count_done[1];
        change_state(WAIT_WDATA, IDLE, count_done[2]);

    end else if (cmd_state[BAD_1] && cmd_data_rdy) begin
        next_rd_mux_aux = 8'hBA;
        change_state(BAD_1, BAD_2);

    end else if (cmd_state[BAD_2] && cmd_data_rdy) begin
        next_rd_mux_aux = 8'hD0;
        change_state(BAD_2, BAD_1);
    end else begin
    end
end

endmodule
