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
// [移植说明] 本文件由 advance-rtl-coding-guidance skill 从 DWC_mipi_csi2_host
// v1.52a 源码提取，作为可独立例化的 IP 库单元。
// - 原文件 include "DWC_mipi_csi2_host_all_rtl_includes.vh" 已移除（本模块
//   不使用其中的任何宏，include 仅为原 SoC 集成上下文所需）。
// - 模块名改为 mpb_elastbuf（与文件名一致），内部无子模块引用。
// - 直接复制本文件到项目 RTL 目录即可综合/仿真。
// - SNPS_ASSERT_ON 断言块仅在定义该宏时编译，综合默认关闭。

//-- Description   : Elasticity buffer
module mpb_elastbuf

    #(//---- PARAMETERS DECLARATION -------------------------------------------
    parameter [31:0] ADDR_DEPTH  = 32'd2,
    parameter [31:0] DATA_WIDTH  = 32'd32
    )

    (//---- PORTS DECLARATION -------------------------------------------------
    input  wire                  clk,     //- clock input
    input  wire                  rstz,    //- asynchronous rstz = reset_n
    input  wire                  write,   //- write enable, active high
    input  wire [DATA_WIDTH-1:0] datain,  //- data input
    input  wire                  read,    //- read enable, active high
    output wire [DATA_WIDTH-1:0] dataout, //- data output

    input  wire                  clrbuff, //- synchronous clear FIFO, active high
    output wire                  emptyz,  //- empty, active low
    output wire                  fullz    //- full, active low
    );

///////////////////////////////////////////////////////////////////////////////
//INTERNAL DECLARATIONS////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
localparam ADDR_DEPTH_BITS = $clog2(ADDR_DEPTH+1);
reg     [ADDR_DEPTH-1:0]    writeptr;
reg     [DATA_WIDTH-1:0]  memshift [ADDR_DEPTH-1:0];
wire    full, empty;
///////////////////////////////////////////////////////////////////////////////
//MAIN FUNCTION////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
//This block implements a serial buffer that has its size parameterizable. The
//buffer is always written from the LSBuffer to the MSBuffer. The last written
//value will always be available in the LSBuffer and a write pointer will be
//used to keep track of the positions that have not yet been filled with data.
//When a read operation is issued the buffer will shift all buffers contents to
//the right and when write operation is issue the content is written in the
//buffers that do not contain data. A write pointer is generated to keep track
//of the buffers that have valid data and the ones that do not.
assign  full     = writeptr[ADDR_DEPTH-1];
assign  fullz    = ~full;
assign  emptyz   = writeptr[0];
assign  empty    = ~emptyz;
assign  dataout  = memshift[0];
///////////////////////////////////////////////////////////////////////////////
//WRITE POINTER GENERATION/////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
//The writeptr contains the information on the buffer that do not contain valid
//data. writeptr is shift register that is filled with ones as the buffers get
//filled with data. This way when hte writeptr pointer contains a register bit
//with a zero it means that the respective buffer position can be written with
//new data.
always @ (posedge clk or negedge rstz)
begin : PROC_writeptr
  if (!rstz) begin
    writeptr[ADDR_DEPTH-1:0]      <= {ADDR_DEPTH{1'b0}};
  end else begin
    if( clrbuff==1'b1 ) begin
      writeptr[ADDR_DEPTH-1:0]    <= {ADDR_DEPTH{1'b0}};
    end else begin
      if (read & (~write)) begin
        writeptr[ADDR_DEPTH-1:0]  <= {1'b0, writeptr[ADDR_DEPTH-1:1]};//read a new value, shift right
      end else if (~read & write) begin
        writeptr[ADDR_DEPTH-1:0]  <= {writeptr[ADDR_DEPTH-2:0], 1'b1};//write a value, shift left
      //ccx_line_cond_begin: ipi_frame_builder.u0.*mpb_elastbuf ; "Corner case, difficult to reproduce and does not correspond to a real usage scenario."
      end else if (read & write) begin                                    //read and write in the same cycle
        //ccx_line_cond_begin: ipi_pipeline.u0.*mpb_elastbuf ; "Unreachable code, by VCS analysis."
        if (full) begin                                                     //if the buffer is full
          writeptr[ADDR_DEPTH-1:0]<= {1'b0, writeptr[ADDR_DEPTH-1:1]};//read a new value, shift right
        //ccx_line_cond_begin: ipi_pipeline.u1.*mpb_elastbuf ; "Unreachable code, by VCS analysis."
        end else if (empty) begin
          writeptr[ADDR_DEPTH-1:0]<= {writeptr[ADDR_DEPTH-2:0], 1'b1};//write a value, shit left
        end
      end
      //ccx_line_cond_end
    end
  end
end// always PROC_writeptr

///////////////////////////////////////////////////////////////////////////////
//MEMORY BUFFERS GENERATION////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
//memshift is a array of memory slots that will define the buffer.
//The MSBuffer is different from all other because since this is the last
//buffer when a shift right is made the shifted content is either a new value
//or a clear value.
generate
genvar i;
for (i=0; i<(ADDR_DEPTH-1); i=i+1)
begin : shift_register
// memshift for oldest words
always @ (posedge clk or negedge rstz)
begin: PROC_memshift_older_words
  if (!rstz) begin
    memshift[i]                   <= {DATA_WIDTH{1'b0}};
//spyglass disable_block SelfDeterminedExpr-ML
//SMD: Self determined expression '******' found
//SJ: Index of vector are being determined through an expression
  end else if((i+1) < ADDR_DEPTH) begin
    if( clrbuff==1'b1 )
        memshift[i]               <= {DATA_WIDTH{1'b0}};
    else begin
      if (read & (~write)) begin                  //read a new value, shift right
        if (writeptr[(i+1)]) begin                //if next position is filled
          memshift[i]             <= memshift[(i+1)];
        end else begin
          memshift[i]             <= {DATA_WIDTH{1'b0}};
        end
      end else if (~read & write) begin           //write a new value
        if (~writeptr[i]) begin                   //if current position is available
          memshift[i]             <= datain;      //else leave it the same
        end
      //ccx_line_cond_begin: ipi_frame_builder.u0.*mpb_elastbuf ; "Corner case, difficult to reproduce and does not correspond to a real usage scenario."
      end else if (read & write) begin            //if read and write in the same cycle
        if (~writeptr[i] | (~writeptr[(i+1)] & writeptr[i])) begin//if the marginal register get
          memshift[i]             <= datain;
        end else begin
          //ccx_line: ipi_pipeline.u0.*mpb_elastbuf ; "Unreachable code, by VCS analysis."
          memshift[i]             <= memshift[(i+1)];//else shift left
        end
      end
      //ccx_line_cond_end
    end
  end
//spyglass enable_block SelfDeterminedExpr-ML
end

end//End of For generate shift_register
endgenerate

// memshift for most recent word
always @ (posedge clk or negedge rstz)
begin: PROC_memshift_MS_word
  if (!rstz) begin
    memshift[ADDR_DEPTH-1] <= {DATA_WIDTH{1'b0}};
  end else begin
    if( clrbuff==1'b1 ) begin
      memshift[ADDR_DEPTH-1] <= {DATA_WIDTH{1'b0}};
    end else begin
      if (read & (~write)) begin                                  //read a new value, shift right
        memshift[ADDR_DEPTH-1]       <= {DATA_WIDTH{1'b0}};
      end else if (~read & write) begin                         //write a new value
        if (~writeptr[ADDR_DEPTH-1]) begin                        //if current position is available
          memshift[ADDR_DEPTH-1]     <= datain;             //else leave it the same
        end
      //ccx_line_cond_begin: ipi_frame_builder.u0.*mpb_elastbuf ; "Corner case, difficult to reproduce and does not correspond to a real usage scenario."
      end else if (read & write) begin                      //if read and write in the same cycle
        if (~writeptr[ADDR_DEPTH-1]) begin                        //if the marginal register get
          memshift[ADDR_DEPTH-1]     <= datain;
        end else begin
          //ccx_line: ipi_pipeline.u0.*mpb_elastbuf ; "Unreachable code, by VCS analysis."
          memshift[ADDR_DEPTH-1]     <= {DATA_WIDTH{1'b0}}; //read has priority
        end
      end
      //ccx_line_cond_end
    end
  end
end


`ifdef SNPS_ASSERT_ON
//Property created to verify that the instantiation is done with the correct value
property elast_buf_size_prop;
@(posedge clk)
  (ADDR_DEPTH>=2);
endproperty
ELAST_BUF_SIZE_ASSERT: assert property (elast_buf_size_prop) else $error("WRONG DEPTH OF ELASTICITY BUFFER ADDR_DEPTH<2!");
`endif

//Revision: $Id: //dwh/mipi_iip/DWC_mipi_csi2_host/main/src/DWC_mipi_csi2_host_mpb_elastbuf.v#12 $
endmodule
