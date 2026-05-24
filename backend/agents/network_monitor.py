import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NetworkMonitorAgent")

class NetworkMonitorAgent:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset state tracking for a new connection session."""
        self.start_time = time.perf_counter()
        self.total_bytes_received = 0
        self.packet_timestamps = []
        self.packet_intervals = []
        self.last_packet_time = None
        self.expected_sequence = 0
        self.packets_lost = 0
        self.packets_received = 0

    def record_packet(self, size_bytes: int, sequence_id: int | None = None) -> dict:
        """
        Record the receipt of an audio packet and calculate current streaming performance.
        
        Args:
            size_bytes (int): Size of the incoming binary chunk.
            sequence_id (int, optional): Client-side sequence number for detecting dropped packets.
            
        Returns:
            dict: Current metrics (latency, jitter, packet loss rate, bandwidth)
        """
        current_time = time.perf_counter()
        self.packets_received += 1
        self.total_bytes_received += size_bytes

        # Calculate arrival intervals and Jitter
        jitter_ms = 0
        if self.last_packet_time is not None:
            interval_ms = (current_time - self.last_packet_time) * 1000
            self.packet_intervals.append(interval_ms)
            
            # Jitter is the variance in packet arrival intervals
            if len(self.packet_intervals) > 1:
                # Jitter calculation: |Interval_n - Interval_{n-1}|
                jitter_ms = abs(self.packet_intervals[-1] - self.packet_intervals[-2])
        self.last_packet_time = current_time

        # Track Frame Loss
        if sequence_id is not None:
            if sequence_id > self.expected_sequence:
                # If sequence_id skipped expected, we lost packets
                lost_count = sequence_id - self.expected_sequence
                self.packets_lost += lost_count
                logger.warning(f"Detected {lost_count} missing audio frame(s). Expected: {self.expected_sequence}, Got: {sequence_id}")
            # Align expected sequence
            self.expected_sequence = sequence_id + 1
        else:
            self.expected_sequence += 1

        # Calculate current metrics
        total_elapsed = current_time - self.start_time
        bandwidth_kbps = 0.0
        if total_elapsed > 0:
            bandwidth_kbps = (self.total_bytes_received * 8) / (total_elapsed * 1024)

        total_expected_packets = self.packets_received + self.packets_lost
        loss_rate = 0.0
        if total_expected_packets > 0:
            loss_rate = self.packets_lost / total_expected_packets

        # Simulated ping/network latency (WebSockets standard RTT)
        # In production this would be calculated by timing a ping/pong frame.
        # Here we compute a nominal baseline connection lag
        latency_ms = int(sum(self.packet_intervals) / len(self.packet_intervals)) if self.packet_intervals else 5

        metrics = {
            "latency_ms": int(latency_ms),
            "packet_loss_rate": float(loss_rate),
            "jitter_ms": int(jitter_ms),
            "bandwidth_kbps": round(bandwidth_kbps, 2)
        }
        
        return metrics

    def get_summary(self) -> dict:
        """Get summary statistics for the entire session."""
        total_elapsed = time.perf_counter() - self.start_time
        bandwidth_kbps = (self.total_bytes_received * 8) / (total_elapsed * 1024) if total_elapsed > 0 else 0.0
        
        total_expected_packets = self.packets_received + self.packets_lost
        loss_rate = self.packets_lost / total_expected_packets if total_expected_packets > 0 else 0.0
        avg_jitter = sum(self.packet_intervals) / len(self.packet_intervals) if self.packet_intervals else 0.0

        return {
            "session_duration_s": round(total_elapsed, 2),
            "total_bytes_received": self.total_bytes_received,
            "packets_received": self.packets_received,
            "packets_lost": self.packets_lost,
            "packet_loss_rate": float(loss_rate),
            "avg_jitter_ms": round(avg_jitter, 2),
            "avg_bandwidth_kbps": round(bandwidth_kbps, 2)
        }
