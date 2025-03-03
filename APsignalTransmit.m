clc;
clear;
close all;

txPluto = sdrtx('Pluto', 'RadioID', 'usb:0', ...  % Use detected RadioID
                'CenterFrequency', 100e6, ...
                'BasebandSampleRate', 1e6, ...
                'Gain', -10);

disp('Transmitting 100 MHz signal...');

% Generate a baseband sine wave signal (e.g., 100 kHz)
fs = 1e6;             % Sample rate
fBaseband = 100e3;    % Baseband frequency (within baseband sampling rate)
t = (0:1023).'/fs;    % Time vector for one frame (transpose to column vector)
signal = exp(1i*2*pi*fBaseband*t); % Complex sine wave (I + jQ)

% Transmit loop
while true
    txPluto(signal);  % Transmit the signal frame
end