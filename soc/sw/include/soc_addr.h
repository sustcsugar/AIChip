/* soc_addr.h — 自动生成，勿手改（source: docs/B2-addr-map.yaml, 节点 B2） */
#ifndef SOC_ADDR_H
#define SOC_ADDR_H

/* 总线域边界 */
#define AXI_BRIDGE_BASE        0x20000000UL

/* 功能窗口基址 */
#define BOOT_ROM_BASE          0x00000000UL  /* size 0x1000 */
#define AXI_SRAM_BASE          0x20000000UL  /* size 0x10000 */
#define UART_BASE              0x40000000UL  /* size 0x1000 */
#define SPI_BASE               0x40001000UL  /* size 0x1000 */
#define IIC_BASE               0x40002000UL  /* size 0x1000 */
#define PWM_BASE               0x40003000UL  /* size 0x1000 */
#define GPIO_BASE              0x40004000UL  /* size 0x1000 */
#define INT_BASE               0x40005000UL  /* size 0x1000 */
#define TIMER_BASE             0x40006000UL  /* size 0x1000 */
#define CLK_RST_BASE           0x40007000UL  /* size 0x1000 */

/* 保留区（访问返回总线错误，仅注释性定义） */
#define RESERVED_MEM_02_BASE   0x00001000UL  /* size 0x1FFFF000 */
#define RESERVED_MEM_04_BASE   0x20010000UL  /* size 0x1FFF0000 */
#define RESERVED_MEM_13_BASE   0x40008000UL  /* size 0xFFF8000 */
#define RESERVED_MEM_15_BASE   0x50000000UL  /* size 0xB0000000 */

/* 译码粒度 4KB */
#define DECODE_GRAN            0x1000UL

#endif /* SOC_ADDR_H */
