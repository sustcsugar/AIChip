// axi_addr_pkg.sv — 自动生成，勿手改（source: docs/B2-addr-map.yaml, 节点 B2）
// 重新生成: python AIFlow/scripts/build_addr_map.py --map docs/B2-addr-map.yaml --out rtl/inc/
package axi_addr_pkg;
    localparam int unsigned ADDR_WIDTH = 32;

    // RIB 域译码边界
    localparam logic [31:0] AXI_BRIDGE_BASE = 32'h2000_0000;  // addr >= 此值经桥

    // 功能窗口
    localparam logic [31:0] BOOT_ROM_BASE          = 32'h00000000;  // size 0x1000
    localparam logic [31:0] AXI_SRAM_BASE          = 32'h20000000;  // size 0x10000
    localparam logic [31:0] UART_BASE              = 32'h40000000;  // size 0x1000
    localparam logic [31:0] SPI_BASE               = 32'h40001000;  // size 0x1000
    localparam logic [31:0] IIC_BASE               = 32'h40002000;  // size 0x1000
    localparam logic [31:0] PWM_BASE               = 32'h40003000;  // size 0x1000
    localparam logic [31:0] GPIO_BASE              = 32'h40004000;  // size 0x1000
    localparam logic [31:0] INT_BASE               = 32'h40005000;  // size 0x1000
    localparam logic [31:0] TIMER_BASE             = 32'h40006000;  // size 0x1000
    localparam logic [31:0] CLK_RST_BASE           = 32'h40007000;  // size 0x1000

    // 保留/未映射区（错误返回）
    localparam logic [31:0] RESERVED_MEM_02_BASE   = 32'h00001000;  // size 0x1FFFF000
    localparam logic [31:0] RESERVED_MEM_04_BASE   = 32'h20010000;  // size 0x1FFF0000
    localparam logic [31:0] RESERVED_MEM_13_BASE   = 32'h40008000;  // size 0xFFF8000
    localparam logic [31:0] RESERVED_MEM_15_BASE   = 32'h50000000;  // size 0xB0000000

    // 译码粒度: 4KB（AXI4 突发不得跨 4KB 边界）
    localparam int unsigned DECODE_GRAN_LOG2 = 12;
endpackage
