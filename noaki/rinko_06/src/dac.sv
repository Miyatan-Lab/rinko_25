module dac(
    input wire clk_27mhz,         // 27MHz FPGA Clock
    input wire reset_n,           // Active low reset
    input wire [15:0] audio_data_in, // 16-bit audio data input (always valid)
    // input wire data_valid,     // Removed: assuming audio_data_in is always valid and updated externally

    output logic bck,             // Bit Clock to PT8211 (Pin 1)
    output logic ws,              // Word Select to PT8211 (Pin 2)
    output logic din              // Data Input to PT8211 (Pin 3)
);

    // --- Parameters ---
    localparam BCK_PERIOD_CYCLES_27MHZ = 2; // 27MHz / 2 = 13.5MHz BCK. Max BCK is 18.4MHz. 
    localparam BITS_PER_CHANNEL = 16;       // 16-bit DAC 
    localparam TOTAL_BITS_PER_WS_CYCLE = BITS_PER_CHANNEL * 2; // 16 bits for Right + 16 bits for Left

    // --- Internal Registers ---
    logic [4:0] bck_toggle_counter; // For BCK generation
    logic [4:0] bit_counter;        // Counts bits within a WS cycle (0 to 31)
    logic [15:0] current_audio_data_shifter; // Holds data for shifting out

    // --- BCK Generation ---
    // BCK toggles at 13.5MHz
    always_ff @(posedge clk_27mhz or negedge reset_n) begin
        if (!reset_n) begin
            bck_toggle_counter <= '0;
            bck <= 0;
        end else begin
            if (bck_toggle_counter == (BCK_PERIOD_CYCLES_27MHZ - 1)) begin
                bck_toggle_counter <= '0;
                bck <= ~bck; // Toggle BCK
            end else begin
                bck_toggle_counter <= bck_toggle_counter + 1;
            end
        end
    end

    // --- WS and DIN Generation ---
    always_ff @(posedge clk_27mhz or negedge reset_n) begin
        if (!reset_n) begin
            ws <= 0; // Start with WS low for Right Channel 
            bit_counter <= '0;
            current_audio_data_shifter <= '0;
            din <= 0;
        end else begin
            // Load new audio data at the beginning of each word cycle
            // This assumes audio_data_in is stable for a whole WS cycle
            // and updates synchronously or asynchronously but prior to the start of a new frame.
            if (bit_counter == 0 && bck_toggle_counter == 0 && bck == 0) begin
                current_audio_data_shifter <= audio_data_in; // Load data for Right Channel
            end
            // Reload for Left channel when bit_counter transitions to 16
            else if (bit_counter == BITS_PER_CHANNEL && bck_toggle_counter == 0 && bck == 0) begin
                current_audio_data_shifter <= audio_data_in; // Load same data for Left Channel
            end

            // Update WS based on bit_counter
            if (bit_counter < BITS_PER_CHANNEL) begin
                ws <= 0; // WS low for Right Channel 
            end else begin
                ws <= 1; // WS high for Left Channel 
            end

            // Shift DIN data on the falling edge of BCK (to ensure stability on rising edge)
            // The PT8211 shifts DIN data on the rising edge of BCK. 
            // Therefore, DIN needs to be stable *before* the rising edge.
            // We update DIN when bck is low and bck_toggle_counter is at half the period, ready for the next bck rising edge.
            if (bck_toggle_counter == (BCK_PERIOD_CYCLES_27MHZ / 2 - 1) && bck == 1) begin // This is when BCK is still high, before it goes low.
                din <= current_audio_data_shifter[BITS_PER_CHANNEL - 1]; // MSB first 
                current_audio_data_shifter <= current_audio_data_shifter << 1; // Shift left for next bit
                bit_counter <= bit_counter + 1;
            end

            // Reset bit_counter for next word cycle after all bits are sent
            if (bit_counter == TOTAL_BITS_PER_WS_CYCLE && bck_toggle_counter == (BCK_PERIOD_CYCLES_27MHZ - 1)) begin
                bit_counter <= 0;
            end
        end
    end

endmodule