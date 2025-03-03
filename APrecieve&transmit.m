clc;
clear;
close all;

%% Initialize the ADALM Pluto Receiver (Pluto 1)
rxPluto = sdrrx('Pluto', 'CenterFrequency', 100e6, ... % Receiver frequency set to 100 MHz
                'BasebandSampleRate', 1e6, ...        % Sample rate
                'SamplesPerFrame', 1024, ...          % Number of samples per frame
                'GainSource', 'AGC Fast Attack', ...  % Automatic Gain Control
                'OutputDataType', 'double');         % Output data type

%% Initialize the ADALM Pluto Transmitter (Pluto 2)
txPluto = sdrtx('Pluto', 'CenterFrequency', 100e6, ... % Transmitter frequency set to 100 MHz
                'BasebandSampleRate', 1e6, ...        % Sample rate
                'Gain', 0, ...
                'ChannelMapping', 1);                 % Use only the first (I) channel for single-channel output

%% Generate a 100 MHz Complex Test Signal (Zero Q Component)
fs = 1e6;  % Sample rate (same as Pluto's sample rate)
t = (0:1/fs:1-1/fs);  % Time vector for 1 second
signal_i = cos(2*pi*100e6*t);  % In-phase (I) component (cosine)

% Create a complex signal with both I and Q components (Q = 0)
signal_complex = signal_i(:) + 1i * zeros(size(signal_i(:)));  % Explicitly complex signal

%% Ensure that the signal has the correct dimensions for single-channel output
% For single-channel output, the signal needs to be a column vector
signal_complex = signal_complex(:);  % Ensure it is a column vector

%% Transmit the Complex Signal (Repeat)
transmitRepeat(txPluto, signal_complex);  % Continuously transmit the complex signal
disp('Pluto 2 is transmitting a 100 MHz signal (complex, zero Q component).');

%% Setup Plot for Real-Time Reception
figure;
h = plot(nan, nan);
title('Received Signal (100 MHz)');
xlabel('Sample Index');
ylabel('Amplitude');
grid on;

%% Real-Time Signal Reception Loop
while true
    % Receive the signal from Pluto 1
    receivedSignal = rxPluto();
    
    % Update the plot with received signal
    set(h, 'XData', 1:length(receivedSignal), 'YData', real(receivedSignal)); % Plot real part
    drawnow;
    
    % Print a message when the signal is detected
    if max(abs(receivedSignal)) > 0.1
        disp('100 MHz Signal Received!');
    else
        disp('No Signal Detected');
    end
    
    % Pause for real-time plotting
    pause(0.1);
end
