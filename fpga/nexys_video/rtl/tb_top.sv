`default_nettype none
module tb_top(
// input wire          ac_adc_sdata,
// input wire          ac_bclk,
// input wire          ac_dac_sdata,
// input wire          ac_lrclk,
// input wire          ac_mclk,
   input wire          btnc,
   input wire          btnd,
   input wire          btnl,
   input wire          btnr,
   input wire          btnu,
   input wire          clk,
   input wire          cpu_resetn,
// input wire          dp_tx_aux_n,
// input wire          dp_tx_aux_p,
// input wire          dp_tx_hpd,
// input wire          eth_int_b,
// input wire          eth_mdc,
// input wire          eth_mdio,
// input wire          eth_pme_b,
// input wire          eth_rst_b,
// input wire          eth_rxck,
// input wire          eth_rxctl,
// input wire [3:0]    eth_rxd,
// input wire          eth_txck,
// input wire          eth_txctl,
// input wire [3:0]    eth_txd,
// input wire          fan_pwm,
// input wire [1:0]    fmc_clk_n,
// input wire [1:0]    fmc_clk_p,
// input wire [33:0]   fmc_la_n,
// input wire [33:0]   fmc_la_p,
// input wire          fmc_mgt_clk_n,
// input wire          fmc_mgt_clk_p,
// input wire          gtp_clk_n,
// input wire          gtp_clk_p,
// input wire          hdmi_rx_cec,
// input wire          hdmi_rx_clk_n,
// input wire          hdmi_rx_clk_p,
// input wire          hdmi_rx_hpa,
// input wire [2:0]    hdmi_rx_n,
// input wire [2:0]    hdmi_rx_p,
// input wire          hdmi_rx_scl,
// input wire          hdmi_rx_sda,
// input wire          hdmi_rx_txen,
// input wire          hdmi_tx_cec,
// input wire          hdmi_tx_clk_n,
// input wire          hdmi_tx_clk_p,
// input wire          hdmi_tx_hpd,
// input wire [2:0]    hdmi_tx_n,
// input wire [2:0]    hdmi_tx_p,
// input wire          hdmi_tx_rscl,
// input wire          hdmi_tx_rsda,
// input wire [7:0]    ja,
// input wire [7:0]    jb,
// input wire [7:0]    jc,
   output logic [7:0]    led,
// input wire          oled_dc,
// input wire          oled_res,
// input wire          oled_sclk,
// input wire          oled_sdin,
// input wire          oled_vbat,
// input wire          oled_vdd,
// input wire          prog_clko,
// input wire [7:0]    prog_d,
// input wire          prog_oen,
// input wire          prog_rdn,
// input wire          prog_rxen,
// input wire          prog_siwun,
// input wire          prog_spien,
// input wire          prog_txen,
// input wire          prog_wrn,
// input wire          ps2_clk,
// input wire          ps2_data,
// input wire          qspi_cs,
// input wire [3:0]    qspi_dq,
// input wire          scl,
// input wire          sd_cclk,
// input wire          sd_cd,
// input wire          sd_cmd,
// input wire [3:0]    sd_d,
// input wire          sd_reset,
// input wire          sda,
// input wire [1:0]    set_vadj,
   input wire [7:0]    sw
// input wire          uart_rx_out,
// input wire          uart_tx_in,
// input wire          vadj_en,
// input wire [3:0]    xa_n,
// input wire [3:0]    xa_p,
);

wire  [31:0]  rd7;
wire  [7:0]   ce;
wire          we;
wire  [31:2] addr;
wire  [31:0] wd;
wire  [3:0]  bytesel;

xilinx_blockram RAM (
       .clkA(clk),
       .enaA(ce[7]),
       .weA(bytesel & {4{we}}),
       .addrA(addr[14:2]),
       .dinA(wd),
       .doutA(rd7)
);

tb_ctl ctl(
    .sysclk(clk),
    .sys_rstn(cpu_resetn),
    .rd0(32'hDEADBEEF),
    .rd1(32'h01234567),
    .rd2(32'hA55AE00E),
    .rd3({btnc, btnd, btnl, btnr, btnu, sw[7:0]}),
    .rd7(rd7),
    .ce(ce),
    .we(we),
    .addr(addr),
    .wd(wd),
    .bytesel(bytesel)
);

logic [7:0] led_values;

always @(posedge clk or negedge cpu_resetn)
    if (!cpu_resetn)
        led_values <= 8'b10101010;
    else if (ce[3] && we)
        led_values <= wd;

assign led = btnc ? sw : led_values;

endmodule
