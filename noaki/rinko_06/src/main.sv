// top_module.sv
module top_module  (
    input wire clk_27mhz, // 27MHz FPGA Clock (e.g., from an oscillator)
    input wire reset_n,   // Active low reset
    input wire uart_rxd,  // UART Receive Data input (connect to external UART Tx pin)

    // PT8211 DAC outputs
    output logic dac_bck, // Bit Clock
    output logic dac_ws,  // Word Select
    output logic dac_din  // Data Input
);
    // Internal wires for connecting modules
    wire [15:0] uart_rx_data;
    wire uart_data_available;

    // Instantiate UART Receiver
    uart_rx uart_receiver_inst (
        .clock          (clk_27mhz),
        .reset          (~reset_n), // uart_rx expects active high reset
        .RxD            (uart_rxd),
        .Rx_buffer      (uart_rx_data),
        .Rx_available   (uart_data_available)
    ); 
    // Register to hold the last received UART data
    logic [15:0] dac_input_data;

    // Logic to latch UART data into DAC input when available
    always_ff @(posedge clk_27mhz or negedge reset_n) begin
        if (!reset_n) begin
            dac_input_data <= 16'b0;
        end else begin
            if (uart_data_available) begin
                dac_input_data <= uart_rx_data; // Latch new data from UART
            end
        end
    end
    // Instantiate DAC Driver
    dac dac_driver_inst (
        .clk_27mhz      (clk_27mhz),
        .reset_n        (reset_n),
        .audio_data_in  (dac_input_data), // Pass the latched UART data to DAC
        .bck            (dac_bck),
        .ws             (dac_ws),
        .din            (dac_din)
    );

endmodule
