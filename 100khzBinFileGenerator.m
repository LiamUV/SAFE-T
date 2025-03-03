clc;
clear;

% Define signal parameters
fs = 1e6;             % Sample rate (set to Pluto's sampling rate)
f = 1e5;              % Signal frequency (set to 100 kHz for correct Nyquist behavior)
t = 0:1/fs:1-1/fs;    % Time vector for 1 second

% Generate the sine wave signal
signal_i = cos(2*pi*f*t);  % In-phase component (I)
signal_q = sin(2*pi*f*t);  % Quadrature component (Q)

% Normalize the signal to fit within int16 range
signal_i = signal_i / max(abs(signal_i));
signal_q = signal_q / max(abs(signal_q));

% Convert to 16-bit integer format
signal_i_int16 = int16(signal_i * 32767);
signal_q_int16 = int16(signal_q * 32767);

% Interleave I and Q data
signal_interleaved = [signal_i_int16; signal_q_int16];
signal_interleaved = signal_interleaved(:); % Convert to column vector

% Save as binary file
fileID = fopen('signal_100kHz.bin', 'w');
fwrite(fileID, signal_interleaved, 'int16');  
fclose(fileID);

disp('Signal file "signal_100kHz.bin" has been generated and saved.');
