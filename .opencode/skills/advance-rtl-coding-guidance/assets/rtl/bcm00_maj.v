
// ------------------------------------------------------------------------------
// 
// Copyright 2021 Synopsys, INC.
// 
// This Synopsys IP and all associated documentation are proprietary to
// Synopsys, Inc. and may only be used pursuant to the terms and conditions of a
// written license agreement with Synopsys, Inc. All other use, reproduction,
// modification, or distribution of the Synopsys IP or the associated
// documentation is strictly prohibited.
// 
// Component Name   : DWC_mipi_csi2_host
// Component Version: 1.52a
// Release Type     : GA
// ------------------------------------------------------------------------------

//
// Filename    : bcm00_maj.v  (原 DWC_mipi_csi2_host_bcm00_maj.v，模块名已与文件名同步)
// Revision    : $Id: //dwh/mipi_iip/DWC_mipi_csi2_host/main/src/DWC_mipi_csi2_host_bcm00_maj.v#4 $
// Author      : Rick Kelly    2/01/06
// Description : bcm00_maj.v Verilog module for DWC_mipi_csi2_host (majority voter)
//
// DesignWare IP ID: 5a6f74f9
//
////////////////////////////////////////////////////////////////////////////////


module bcm00_maj (
    a,
    b,
    c,
    z
    );

parameter integer WIDTH        = 1;  // RANGE 1 to 8192


input  [WIDTH-1:0]      a;    // 1st voter data input bus
input  [WIDTH-1:0]      b;    // 2nd voter data input bus
input  [WIDTH-1:0]      c;    // 3rd voter data input bus
output [WIDTH-1:0]      z;    // majority voted data output bus

// spyglass disable_block Ac_conv01
// SMD: Synchronized sequential element(s) converge on combinational logic
// SJ: The single-bit signals converging into sequential elements are triplicated from the same signal at the source and run through parallel paths of synchronizers with the identical number of stages.  This synchronized convergence is intentional and directly supplies combinational logic that produces a majority vote result which is immune to non-gray code transitions.
// spyglass disable_block Ac_conv02
// SMD: Synchronizers converge on combinational logic
// SJ: The single-bit signals converging into the combinational logic are triplicated from the same signal at the source and run through parallel paths of synchronizers with the identical number of stages.  This synchronized convergence is intentional as the combinational logic produces a majority vote result which is immune to non-gray code transitions.
`ifdef DWC_MAJORITY_VOTE_CELL_SRC
  `DWC_MAJORITY_VOTE_CELL_SRC
`else
  assign z = (a & b) | (a & c) | (b & c);
`endif
// spyglass enable_block Ac_conv01
// spyglass enable_block Ac_conv02

endmodule
