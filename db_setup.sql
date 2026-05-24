-- SQL Script for MySQL Workbench
-- Miranet VoiceAgent Database Setup and Synthetic Data

-- 1. Create Database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `miranet_voiceagent`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `miranet_voiceagent`;

-- 2. Drop existing tables if you want a clean start (Optional, commented out)
-- DROP TABLE IF EXISTS `network_metrics`;
-- DROP TABLE IF EXISTS `voice_logs`;
-- DROP TABLE IF EXISTS `conversations`;

-- 3. Create Tables
CREATE TABLE IF NOT EXISTS `conversations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` VARCHAR(255) UNIQUE NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `voice_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` VARCHAR(255) NOT NULL,
    `sequence_number` INT NOT NULL,
    `audio_size_bytes` INT NOT NULL,
    `transcription` TEXT,
    `classification_intent` VARCHAR(255),
    `classification_sentiment` VARCHAR(255),
    `response_text` TEXT,
    `transcription_latency_ms` INT,
    `classification_latency_ms` INT,
    `response_latency_ms` INT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`session_id`) REFERENCES `conversations`(`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `network_metrics` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `session_id` VARCHAR(255) NOT NULL,
    `latency_ms` INT,
    `packet_loss_rate` FLOAT,
    `jitter_ms` INT,
    `bandwidth_kbps` FLOAT,
    `recorded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`session_id`) REFERENCES `conversations`(`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Insert Synthetic Data for Testing
-- Insert active sessions
INSERT INTO `conversations` (`session_id`, `created_at`) VALUES
('session_diego_001', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
('session_sergio_002', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
('session_test_003', DATE_SUB(NOW(), INTERVAL 10 MINUTE))
ON DUPLICATE KEY UPDATE `session_id` = `session_id`;

-- Insert voice logs for Session 1 (Diego - Technical Support)
INSERT INTO `voice_logs` 
(`session_id`, `sequence_number`, `audio_size_bytes`, `transcription`, `classification_intent`, `classification_sentiment`, `response_text`, `transcription_latency_ms`, `classification_latency_ms`, `response_latency_ms`, `created_at`)
VALUES
('session_diego_001', 1, 64000, 
 'Hola, buenas tardes. Tengo un problema con el internet de mi oficina, está sumamente lento.', 
 'soporte_tecnico', 'frustrado', 
 'Hola, lamento escuchar que tu internet está lento. Para poder ayudarte, ¿me confirmas si estás conectado por cable o por Wi-Fi?', 
 850, 420, 1100, DATE_SUB(NOW(), INTERVAL 115 MINUTE)),
 
('session_diego_001', 2, 48000, 
 'Estoy conectado directamente por cable de red al módem y aun así demora en cargar todo.', 
 'soporte_tecnico', 'neutral', 
 'Entendido. Procederé a realizar una prueba de ping y refresco de señal desde la central hacia tu módem. Demorará unos segundos.', 
 720, 390, 950, DATE_SUB(NOW(), INTERVAL 114 MINUTE)),
 
('session_diego_001', 3, 52000, 
 'De acuerdo, espero. Avísame cuando termines el reinicio de señal.', 
 'soporte_tecnico', 'neutral', 
 'Señal refrescada correctamente. Por favor, verifica si la velocidad ha mejorado. Si persiste la lentitud, agendaremos una visita técnica.', 
 680, 310, 880, DATE_SUB(NOW(), INTERVAL 113 MINUTE));

-- Insert voice logs for Session 2 (Sergio - Billing & Payments Inquiry)
INSERT INTO `voice_logs` 
(`session_id`, `sequence_number`, `audio_size_bytes`, `transcription`, `classification_intent`, `classification_sentiment`, `response_text`, `transcription_latency_ms`, `classification_latency_ms`, `response_latency_ms`, `created_at`)
VALUES
('session_sergio_002', 1, 80000, 
 'Hola, quería consultar cuál es mi saldo a pagar este mes y cuándo es mi fecha límite.', 
 'consulta_saldo', 'neutral', 
 'Hola Sergio. Tu saldo al día de hoy es de 120 soles y tu fecha límite de pago es el 30 de este mes.', 
 920, 350, 1020, DATE_SUB(NOW(), INTERVAL 55 MINUTE)),
 
('session_sergio_002', 2, 75000, 
 'Excelente, muchas gracias. ¿Hay algún cargo adicional por pagar fuera de tiempo?', 
 'consulta_saldo', 'neutral', 
 'Sí, los pagos tardíos tienen un recargo por mora del cinco por ciento del total del recibo. Te sugerimos realizar el pago antes de la fecha límite.', 
 890, 380, 1150, DATE_SUB(NOW(), INTERVAL 54 MINUTE));

-- Insert network metrics for Session 1 (Diego - Bad Connection)
INSERT INTO `network_metrics`
(`session_id`, `latency_ms`, `packet_loss_rate`, `jitter_ms`, `bandwidth_kbps`, `recorded_at`)
VALUES
('session_diego_001', 120, 0.05, 18, 96.5, DATE_SUB(NOW(), INTERVAL 115 MINUTE)),
('session_diego_001', 145, 0.08, 22, 64.2, DATE_SUB(NOW(), INTERVAL 114 MINUTE)),
('session_diego_001', 98, 0.02, 11, 128.0, DATE_SUB(NOW(), INTERVAL 113 MINUTE));

-- Insert network metrics for Session 2 (Sergio - Stable Connection)
INSERT INTO `network_metrics`
(`session_id`, `latency_ms`, `packet_loss_rate`, `jitter_ms`, `bandwidth_kbps`, `recorded_at`)
VALUES
('session_sergio_002', 45, 0.00, 3, 256.0, DATE_SUB(NOW(), INTERVAL 55 MINUTE)),
('session_sergio_002', 48, 0.00, 4, 256.0, DATE_SUB(NOW(), INTERVAL 54 MINUTE));

-- Insert network metrics for Session 3 (Test Session)
INSERT INTO `network_metrics`
(`session_id`, `latency_ms`, `packet_loss_rate`, `jitter_ms`, `bandwidth_kbps`, `recorded_at`)
VALUES
('session_test_003', 30, 0.00, 2, 512.0, DATE_SUB(NOW(), INTERVAL 10 MINUTE));
