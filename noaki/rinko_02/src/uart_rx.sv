module uart_rx(
    input clock,
    input reset,
    input RxD,
    output logic [15:0] Rx_buffer,  // Changed to 16-bit
    output logic Rx_available
);
parameter baud_rate=9600;

// FPGAのクロック周波数/ボーレイト
parameter baud_div=(27000000/baud_rate)-1;

// 信号のハラのぶぶん (center of the bit period)
parameter valid=baud_div/2;

// マシンのステート
typedef enum logic {
    idle=0,
    trns=1
} uart_state;

logic [11:0] Rx_baud_counter; // Counter for baud rate division
logic [4:0] Rx_bit_counter;  // Changed to accommodate up to 18 bits (1 start + 16 data + 1 stop)
logic Rx_prev;               // Previous state of RxD for edge detection
wire Rx_strt;               // Detects start bit
wire Rx_trig;               // Triggers at the center of each bit
logic [17:0] Rx_queue;       // Changed to 16 data bits + 1 start bit + 1 stop bit
uart_state Rx_state;

// Rx立下り検知 (Detect falling edge on RxD for start bit)
assign Rx_strt = (Rx_state==idle && Rx_prev==1 && RxD==0) ? 1'b1 : 1'b0;

always@(posedge clock or negedge reset)begin
    if(!reset) Rx_prev <= 1'b1;
    else Rx_prev <= RxD;
end

always @(posedge clock or negedge reset) begin
    if(!reset) Rx_baud_counter <= 12'b0;
    else begin
        // Reset counter on start bit detection or when baud_div is reached
        if (Rx_strt || Rx_baud_counter == baud_div) begin
            Rx_baud_counter <= 12'b0;
        end else begin
            Rx_baud_counter <= Rx_baud_counter + 1'b1;
        end
    end
end

// Rx_trig: Trigger when Rx_baud_counter reaches the 'valid' point (center of the bit)
assign Rx_trig = (valid == Rx_baud_counter) ? 1'b1 : 1'b0;

always_ff@(posedge clock or negedge reset)begin
    if(!reset)begin
        Rx_bit_counter <= 5'b0;
        Rx_state <= idle;
        Rx_available <= 1'b0;
        Rx_buffer <= 16'b0; // Initialize Rx_buffer
        Rx_queue <= 18'b0;  // Initialize Rx_queue
    end
    else begin
        case(Rx_state)
            idle: begin
                Rx_available <= 1'b0; // Clear Rx_available when idle
                if(Rx_strt)begin
                    Rx_state <= trns;
                    Rx_bit_counter <= 5'b0; // Reset bit counter
                end
            end
            trns: begin
                if(Rx_trig)begin
                    // Store the received bit into the queue
                    Rx_queue[Rx_bit_counter] <= RxD;
                    Rx_bit_counter <= Rx_bit_counter + 1'b1; // Increment bit counter

                    // Check if all 16 data bits + 1 start bit + 1 stop bit have been received
                    // Total bits: 1 (start) + 16 (data) + 1 (stop) = 18 bits.
                    // Rx_bit_counter will go from 0 to 17.
                    if(Rx_bit_counter == 17) begin // After receiving the 18th bit (the stop bit)
                        Rx_state <= idle; // Go back to idle state
                        // Data bits are from index 1 to 16 in Rx_queue (Rx_queue[16:1])
                        // Assuming LSB first, Rx_queue[1] is the first data bit, Rx_queue[16] is the last.
                        // If MSB first, you would need to reverse the order.
                        // Standard UART is LSB first.
                        Rx_buffer <= Rx_queue[16:1]; // Extract 16 data bits
                        Rx_available <= 1'b1; // Indicate new data is available
                    end
                end
            end
            default: Rx_state <= idle; // Should not happen, but for completeness
        endcase
    end
end
endmodule